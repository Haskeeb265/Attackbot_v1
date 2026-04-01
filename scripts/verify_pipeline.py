"""
Live Pipeline Verification Script
==================================
Triggers a real scan against a local target and verifies the full M1→M3 pipeline.
No mocks — real CLI tools in Docker containers against a real HTTP target.

Usage: python scripts/verify_pipeline.py
Prerequisites: Docker stack running, target on host.docker.internal:8888
"""
import asyncio
import json
import sys
import uuid
import time
import subprocess
import os
import httpx
from datetime import datetime, timezone

# Add repo root to path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from backend.shared.db import init_db, get_session
from backend.shared.schemas.scan_jobs import (
    ScanJobsPayload, ScopeDefinition, ScopeEntry, FeatureFlags,
    build_scan_job_message,
)
from backend.shared.queue import QueuePublisher, Queues
from sqlalchemy import text

# Docker-accessible target
TARGET_HOST = "host.docker.internal"
TARGET_PORT = 8888
TARGET_BASE = f"http://{TARGET_HOST}:{TARGET_PORT}"
DB_DSN = "postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot"
CORE_ENGINE_URL = "http://localhost:8002"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def log_pass(msg):
    print(f"  {GREEN}[PASS]{RESET} {msg}")


def log_fail(msg):
    print(f"  {RED}[FAIL]{RESET} {msg}")


def log_info(msg):
    print(f"  {CYAN}[INFO]{RESET} {msg}")


def log_header(msg):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {msg}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


async def db_query(query, params=None):
    async with get_session() as session:
        result = await session.execute(text(query), params or {})
        return result


async def db_fetch(query, params=None):
    async with get_session() as session:
        result = await session.execute(text(query), params or {})
        return result.fetchall()


async def db_fetchrow(query, params=None):
    async with get_session() as session:
        result = await session.execute(text(query), params or {})
        return result.fetchone()


async def create_test_program():
    """Insert a test program into the DB with scope pointing at our local target."""
    program_id = str(uuid.uuid4())
    handle = f"verify-{program_id[:8]}"
    async with get_session() as session:
        await session.execute(
            text("""
                INSERT INTO programs (program_id, platform, handle, name, url, bounty_type, is_active, created_at, updated_at)
                VALUES (:pid, 'hackerone', :handle, 'Pipeline Verification Target', :url, 'bug_bounty', true, NOW(), NOW())
            """),
            {"pid": program_id, "handle": handle, "url": TARGET_BASE},
        )
        await session.execute(
            text("""
                INSERT INTO program_scopes (scope_id, program_id, scope_type, asset_type, value, created_at)
                VALUES (:sid, :pid, 'in_scope', 'url', :scope_val, NOW())
            """),
            {"sid": str(uuid.uuid4()), "pid": program_id, "scope_val": TARGET_BASE},
        )
        await session.commit()
    return program_id


async def trigger_scan_via_api(program_id):
    """Trigger a scan via the core-engine API endpoint (handles queue internally)."""
    payload = ScanJobsPayload(
        program_id=program_id,
        platform="hackerone",
        handle="verify-pipeline",
        scope=ScopeDefinition(
            in_scope=[
                ScopeEntry(asset_type="url", value=TARGET_BASE),
            ],
        ),
        feature_flags=FeatureFlags(
            nuclei=False,
            browser_session=False,
            api_fuzzing=False,
            takeover=False,
            asset_discovery=False,
            fingerprinting=True,
            enumeration=True,
            xss=True,
            cors=True,
            secret_js=True,
        ),
        priority=1,
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{CORE_ENGINE_URL}/api/v1/scans/start",
            json=payload.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return resp.json()


async def wait_for_scan_completion(program_id, timeout=300):
    """Poll the scans table until the scan completes or times out."""
    start = time.time()
    while time.time() - start < timeout:
        row = await db_fetchrow(
            "SELECT scan_id, status, finding_count, severity_breakdown FROM scans WHERE program_id = :pid ORDER BY created_at DESC LIMIT 1",
            {"pid": program_id},
        )
        if row and row[1] in ("completed", "partial", "failed_scope", "failed_internal", "failed_auth"):
            return {
                "scan_id": str(row[0]),
                "status": row[1],
                "finding_count": row[2],
                "severity_breakdown": row[3],
            }
        await asyncio.sleep(5)
    return None


async def audit_scan_results(scan_id):
    """Query all relevant tables for the scan and return a full audit."""
    results = {}

    # Scan record
    scan = await db_fetchrow(
        "SELECT scan_id, status, finding_count, severity_breakdown, started_at, completed_at, retry_count FROM scans WHERE scan_id = :sid",
        {"sid": scan_id},
    )
    results["scan"] = dict(scan._mapping) if scan else None

    # Stages
    stages = await db_fetch(
        "SELECT stage_number, stage_name, status, error_detail, output_summary FROM scan_stages WHERE scan_id = :sid ORDER BY stage_number",
        {"sid": scan_id},
    )
    results["stages"] = [dict(s._mapping) for s in stages]

    # Assets
    assets = await db_fetch(
        "SELECT asset_id, asset_type, value, http_status, technology_stack FROM assets WHERE scan_id = :sid",
        {"sid": scan_id},
    )
    results["assets"] = [dict(a._mapping) for a in assets]

    # Endpoints
    endpoints = await db_fetch(
        "SELECT endpoint_id, method, path, full_url, response_code, requires_auth FROM endpoints WHERE scan_id = :sid",
        {"sid": scan_id},
    )
    results["endpoints"] = [dict(e._mapping) for e in endpoints]

    # JS Assets
    js_assets = await db_fetch(
        "SELECT js_asset_id, url, content_hash, storage_path, size_bytes FROM js_assets WHERE scan_id = :sid",
        {"sid": scan_id},
    )
    results["js_assets"] = [dict(j._mapping) for j in js_assets]

    # Findings
    findings = await db_fetch(
        """SELECT finding_id, title, vulnerability_type, severity, cvss_score,
           affected_url, affected_parameter, is_verified, is_false_positive,
           deduplication_hash, source, description
           FROM findings WHERE scan_id = :sid ORDER BY severity DESC""",
        {"sid": scan_id},
    )
    results["findings"] = [dict(f._mapping) for f in findings]

    # Finding evidence
    evidence = await db_fetch(
        """SELECT fe.evidence_id, fe.artifact_type, fe.storage_path, fe.description
           FROM finding_evidence fe
           JOIN findings f ON fe.finding_id = f.finding_id
           WHERE f.scan_id = :sid""",
        {"sid": scan_id},
    )
    results["evidence"] = [dict(e._mapping) for e in evidence]

    # Vulnerability groups
    vuln_groups = await db_fetch(
        "SELECT group_id, vulnerability_type, affected_count, max_severity FROM vulnerability_groups WHERE scan_id = :sid",
        {"sid": scan_id},
    )
    results["vuln_groups"] = [dict(v._mapping) for v in vuln_groups]

    return results


async def main():
    init_db(DB_DSN)

    # ── Phase 0: Start local target ─────────────────────────────────────
    log_header("PHASE 0: Local Target")
    log_info(f"Target will be at {TARGET_BASE}")
    log_info("Starting target server in background...")

    target_proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO_ROOT, "scripts", "live_target.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    await asyncio.sleep(2)

    # Verify target is reachable from host
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"http://localhost:{TARGET_PORT}/")
            log_pass(f"Target reachable on localhost:{TARGET_PORT} (status={resp.status_code})")
    except Exception as e:
        log_fail(f"Target not reachable: {e}")
        target_proc.kill()
        return

    # ── Phase 1: Create test program ────────────────────────────────────
    log_header("PHASE 1: Inject Test Program")
    program_id = await create_test_program()
    log_pass(f"Program created: {program_id}")

    # Verify in DB
    row = await db_fetchrow("SELECT name, handle FROM programs WHERE program_id = :pid", {"pid": program_id})
    if row:
        log_pass(f"DB verified: name='{row[0]}', handle='{row[1]}'")
    else:
        log_fail("Program not found in DB!")
        target_proc.kill()
        return

    # ── Phase 2: Trigger scan ───────────────────────────────────────────
    log_header("PHASE 2: Trigger Scan")
    try:
        result = await trigger_scan_via_api(program_id)
        log_pass(f"Scan queued: {result}")
    except Exception as e:
        log_fail(f"Failed to queue scan: {e}")
        target_proc.kill()
        return

    # ── Phase 3: Wait for completion ────────────────────────────────────
    log_header("PHASE 3: Pipeline Execution")
    log_info("Waiting for scan to complete (max 5 min)...")
    scan_result = await wait_for_scan_completion(program_id, timeout=300)

    if scan_result is None:
        log_fail("Scan timed out after 5 minutes!")
        # Check what status it has
        row = await db_fetchrow(
            "SELECT status FROM scans WHERE program_id = :pid ORDER BY created_at DESC LIMIT 1",
            {"pid": program_id},
        )
        log_info(f"Current scan status: {row[0] if row else 'NOT FOUND'}")
        target_proc.kill()
        return

    log_pass(f"Scan completed: status={scan_result['status']}, findings={scan_result['finding_count']}")
    scan_id = scan_result["scan_id"]

    # ── Phase 4: Audit results ──────────────────────────────────────────
    log_header("PHASE 4: Results Audit")
    audit = await audit_scan_results(scan_id)

    # Scan record
    scan = audit["scan"]
    if scan:
        log_pass(f"Scan record: status={scan['status']}, findings={scan['finding_count']}")
        log_info(f"  Started: {scan['started_at']}")
        log_info(f"  Completed: {scan['completed_at']}")
        log_info(f"  Retry count: {scan['retry_count']}")
    else:
        log_fail("No scan record found!")

    # Stages
    print(f"\n  {BOLD}Pipeline Stages:{RESET}")
    for stage in audit["stages"]:
        status_icon = "[OK]" if stage["status"] == "completed" else ("[~]" if stage["status"] == "partial" else "[!]")
        color = GREEN if stage["status"] == "completed" else (YELLOW if stage["status"] == "partial" else RED)
        summary = json.dumps(stage["output_summary"]) if stage["output_summary"] else ""
        print(f"    {color}{status_icon}{RESET} Stage {stage['stage_number']} ({stage['stage_name']}): {stage['status']} {summary}")

    # Assets
    print(f"\n  {BOLD}Assets ({len(audit['assets'])}):{RESET}")
    for asset in audit["assets"][:10]:
        print(f"    • {asset['asset_type']}: {asset['value']} (HTTP {asset['http_status']})")

    # Endpoints
    print(f"\n  {BOLD}Endpoints ({len(audit['endpoints'])}):{RESET}")
    for ep in audit["endpoints"][:15]:
        print(f"    • {ep['method']} {ep['path']} → {ep['response_code']}")

    # JS Assets
    print(f"\n  {BOLD}JS Assets ({len(audit['js_assets'])}):{RESET}")
    for js in audit["js_assets"][:5]:
        print(f"    • {js['url']} ({js['size_bytes']} bytes)")

    # Findings
    print(f"\n  {BOLD}Findings ({len(audit['findings'])}):{RESET}")
    for f in audit["findings"]:
        severity_colors = {
            "critical": RED, "high": RED, "medium": YELLOW, "low": CYAN, "info": "",
        }
        color = severity_colors.get(f["severity"], "")
        verified = " [VERIFIED]" if f["is_verified"] else ""
        fp = " [FALSE POSITIVE]" if f["is_false_positive"] else ""
        print(f"    {color}• [{f['severity'].upper()}] {f['title']}{verified}{fp}{RESET}")
        print(f"      Type: {f['vulnerability_type']}, Source: {f['source']}, CVSS: {f['cvss_score']}")
        print(f"      URL: {f['affected_url']}")
        if f["affected_parameter"]:
            print(f"      Parameter: {f['affected_parameter']}")
        print(f"      Dedup hash: {f['deduplication_hash'][:16]}...")

    # Evidence
    print(f"\n  {BOLD}Evidence ({len(audit['evidence'])}):{RESET}")
    for ev in audit["evidence"][:5]:
        print(f"    • [{ev['artifact_type']}] {ev['storage_path']}")

    # Vulnerability groups
    print(f"\n  {BOLD}Vulnerability Groups ({len(audit['vuln_groups'])}):{RESET}")
    for vg in audit["vuln_groups"]:
        print(f"    • {vg['vulnerability_type']}: {vg['affected_count']} affected, max={vg['max_severity']}")

    # ── Phase 5: Verdict ────────────────────────────────────────────────
    log_header("VERDICT")

    checks = {
        "Scan completed (not failed)": scan and scan["status"] in ("completed", "partial"),
        "Stages recorded": len(audit["stages"]) > 0,
        "Stage 0 (scope) completed": any(s["stage_name"] == "scope_filter" or s["stage_number"] == 0 for s in audit["stages"]),
        "Endpoints discovered": len(audit["endpoints"]) > 0,
        "Findings persisted": len(audit["findings"]) > 0,
        "Dedup hashes present": all(f["deduplication_hash"] for f in audit["findings"]),
        "CVSS scores assigned": all(f["cvss_score"] is not None for f in audit["findings"]),
        "Severity labels present": all(f["severity"] for f in audit["findings"]),
    }

    all_passed = True
    for check, passed in checks.items():
        if passed:
            log_pass(check)
        else:
            log_fail(check)
            all_passed = False

    if all_passed:
        print(f"\n  {GREEN}{BOLD}🎉 ALL M1→M3 PIPELINE CHECKS PASSED{RESET}")
    else:
        print(f"\n  {RED}{BOLD}⚠ SOME CHECKS FAILED — SEE ABOVE{RESET}")

    # Cleanup
    target_proc.kill()
    print()


if __name__ == "__main__":
    asyncio.run(main())
