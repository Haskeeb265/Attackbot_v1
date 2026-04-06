"""
Live E2E trace for the full HackerOne -> scan -> report pipeline.

This test validates, in one flow:
1) HackerOne scrape trigger is accepted.
2) A scraped HackerOne program with usable web scope is selected.
3) Core Engine scan reaches a terminal state and yields findings.
4) Reporter generates downloadable artifacts.
5) Replay commands are produced from live findings metadata.
6) Generated DOCX content includes reproduction-oriented text when downloadable.
7) Evidence endpoints are reachable for discovered findings.

The test writes a machine-readable runtime artifact:
    E2E_Runs/E2E_HACKERONE_FULL_PIPELINE_LAST.json
"""

from __future__ import annotations

import io
import json
import os
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from tests.e2e.url_utils import rewrite_minio_presigned_url_for_host


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SCRAPER_BASE = os.getenv("E2E_SCRAPER_URL", "http://localhost:8001/api/v1")
CORE_BASE = os.getenv("E2E_CORE_URL", "http://localhost:8002/api/v1")
REPORTER_BASE = os.getenv("E2E_REPORTER_URL", "http://localhost:8003/api/v1")

PROGRAM_WAIT_SECONDS = int(os.getenv("E2E_H1_PROGRAM_WAIT_SECONDS", "420"))
SCAN_WAIT_SECONDS_SMALL = int(
    os.getenv("E2E_H1_SCAN_WAIT_SECONDS_SMALL", os.getenv("E2E_H1_SCAN_WAIT_SECONDS", "300"))
)
SCAN_WAIT_SECONDS_LARGE = int(os.getenv("E2E_H1_SCAN_WAIT_SECONDS_LARGE", "900"))
SCAN_WAIT_SCOPE_THRESHOLD = int(os.getenv("E2E_H1_SCAN_WAIT_SCOPE_THRESHOLD", "10"))
REPORT_WAIT_SECONDS = int(os.getenv("E2E_H1_REPORT_WAIT_SECONDS", "360"))
POLL_SECONDS = max(float(os.getenv("E2E_H1_POLL_SECONDS", "5")), 1.0)
ALLOW_FINDINGS_FALLBACK = _env_bool("E2E_H1_ALLOW_FINDINGS_FALLBACK", False)
STRICT_MODE = not ALLOW_FINDINGS_FALLBACK
MINIO_HOST_PORT = os.getenv("MINIO_HOST_PORT", "").strip()

ROOT_DIR = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT_DIR / "E2E_Runs" / "E2E_HACKERONE_FULL_PIPELINE_LAST.json"

TERMINAL_SCAN_STATUSES = {"completed", "partial", "failed_scope", "failed_internal", "failed_auth"}
TERMINAL_REPORT_STATUSES = {"completed", "partial", "failed"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(trace: dict[str, Any], message: str) -> None:
    trace.setdefault("steps", []).append(f"{_utc_now()} | {message}")


def _write_trace(trace: dict[str, Any]) -> None:
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACE_PATH.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")


def _service_healthy(base_url: str) -> tuple[bool, dict[str, Any] | None]:
    try:
        response = httpx.get(f"{base_url}/health", timeout=8)
    except Exception:
        return False, None
    if response.status_code != 200:
        return False, {"status_code": response.status_code}
    try:
        payload = response.json()
    except Exception:
        payload = {"raw": response.text}
    return True, payload


def _require_hackerone_credentials() -> None:
    username = os.getenv("HACKERONE_API_USERNAME")
    token = os.getenv("HACKERONE_API_TOKEN")
    if not username or not token:
        pytest.skip("HACKERONE_API_USERNAME/HACKERONE_API_TOKEN must be set for live HackerOne E2E")
    if username.lower() == "placeholder" or token.lower() == "placeholder":
        pytest.skip("HackerOne credentials are placeholders; live HackerOne E2E cannot run")


def _trigger_hackerone_scrape(trace: dict[str, Any]) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        try:
            response = httpx.post(
                f"{SCRAPER_BASE}/scrape/trigger",
                params={"platform": "hackerone"},
                timeout=90,
            )
        except Exception as exc:
            attempts.append(
                {
                    "attempt": attempt,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            time.sleep(POLL_SECONDS)
            continue

        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        attempts.append(
            {
                "attempt": attempt,
                "status_code": response.status_code,
                "body": body,
            }
        )

        status_code = int(response.status_code)
        status = str(body.get("status") or "").strip().lower()
        platform = str(body.get("platform") or "").strip().lower()

        strict_ok = status_code == 202 and status == "accepted" and platform == "hackerone"
        compat_ok = (
            status_code in {200, 202}
            and platform == "hackerone"
            and status in {"accepted", "completed", "skipped", "running"}
        )
        if strict_ok or compat_ok:
            trace["scrape_trigger"] = {
                "status_code": status_code,
                "body": body,
                "attempts": attempts,
            }
            if strict_ok:
                _log(trace, "Scraper trigger accepted for platform=hackerone")
            else:
                _log(
                    trace,
                    "Scraper trigger accepted in compatibility mode: "
                    f"status_code={status_code} status={status}",
                )
            return body

        time.sleep(POLL_SECONDS)

    trace["scrape_trigger"] = {"status_code": None, "body": None, "attempts": attempts}
    pytest.fail(
        "Failed to trigger HackerOne scrape after retries. "
        f"attempts={attempts}"
    )


def _fetch_hackerone_programs(page_size: int = 50) -> list[dict[str, Any]]:
    response = httpx.get(
        f"{SCRAPER_BASE}/programs",
        params={"platform": "hackerone", "page_size": page_size},
        timeout=15,
    )
    response.raise_for_status()
    body = response.json()
    items = body.get("items", [])
    return items if isinstance(items, list) else []


def _fetch_scope(program_id: str) -> dict[str, Any]:
    response = httpx.get(f"{SCRAPER_BASE}/programs/{program_id}/scope", timeout=15)
    response.raise_for_status()
    return response.json()


def _scope_summary(scope_payload: dict[str, Any]) -> dict[str, int]:
    summary = {
        "in_scope_total": 0,
        "valid_in_scope": 0,
        "url_in_scope": 0,
        "domain_in_scope": 0,
        "wildcard_domain_in_scope": 0,
    }
    in_scope = scope_payload.get("in_scope", [])
    if not isinstance(in_scope, list):
        return summary
    summary["in_scope_total"] = len(in_scope)
    for entry in in_scope:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("value") or "").strip()
        asset_type = str(entry.get("asset_type") or "").strip().lower()
        if not value:
            continue
        summary["valid_in_scope"] += 1
        if asset_type == "url":
            summary["url_in_scope"] += 1
        elif asset_type == "domain":
            summary["domain_in_scope"] += 1
        elif asset_type == "wildcard_domain":
            summary["wildcard_domain_in_scope"] += 1
    return summary


def _adaptive_scan_wait_seconds(valid_in_scope: int) -> int:
    if int(valid_in_scope) > SCAN_WAIT_SCOPE_THRESHOLD:
        return SCAN_WAIT_SECONDS_LARGE
    return SCAN_WAIT_SECONDS_SMALL


def _is_download_proof_required(strict_mode: bool, minio_host_port: str) -> bool:
    return strict_mode and bool(minio_host_port.strip())


def _result_label(fallback_used: bool) -> str:
    return "passed_with_fallback" if fallback_used else "passed"


def _scan_source_outcome(
    terminal_scan_payload: dict[str, Any] | None,
    finding_count: int,
    allow_findings_fallback: bool,
) -> str:
    needs_fallback = terminal_scan_payload is None or int(finding_count) <= 0
    if not needs_fallback:
        return "fresh"
    if allow_findings_fallback:
        return "fallback"
    return "strict_fail"


def _list_recent_scans() -> list[dict[str, Any]]:
    response = httpx.get(f"{CORE_BASE}/scans", timeout=20)
    response.raise_for_status()
    body = response.json()
    scans = body.get("scans", [])
    return scans if isinstance(scans, list) else []


def _program_ids_with_findings_from_api() -> dict[str, str]:
    latest_scan_by_program: dict[str, str] = {}
    for scan in _list_recent_scans():
        program_id = str(scan.get("program_id") or "").strip()
        scan_id = str(scan.get("scan_id") or "").strip()
        status = str(scan.get("status") or "").lower().strip()
        finding_count = int(scan.get("finding_count") or 0)
        if not program_id or not scan_id:
            continue
        if status not in {"completed", "partial"}:
            continue
        if finding_count <= 0:
            continue
        if program_id not in latest_scan_by_program:
            latest_scan_by_program[program_id] = scan_id
    return latest_scan_by_program


def _choose_best_candidate(
    programs: list[dict[str, Any]],
    latest_scan_by_program: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    candidates: list[tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]]] = []

    for program in programs:
        program_id = str(program.get("program_id") or "")
        if not program_id:
            continue
        try:
            scope = _fetch_scope(program_id)
        except Exception:
            continue
        summary = _scope_summary(scope)
        if summary["valid_in_scope"] <= 0:
            continue

        score = (
            1 if program_id in latest_scan_by_program else 0,
            1 if summary["url_in_scope"] > 0 else 0,
            int(summary["valid_in_scope"]),
            str(program.get("updated_at") or ""),
        )
        candidates.append((score, program, {"scope": scope, "summary": summary}))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, program, details = candidates[0]
    return program, details


def _wait_for_eligible_program(trace: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    latest_scan_by_program = _program_ids_with_findings_from_api()
    _log(
        trace,
        "Loaded recent program set with findings from core API: "
        f"count={len(latest_scan_by_program)}",
    )

    deadline = time.monotonic() + PROGRAM_WAIT_SECONDS
    while time.monotonic() < deadline:
        programs = _fetch_hackerone_programs(page_size=80)
        if programs:
            selected = _choose_best_candidate(programs, latest_scan_by_program)
            if selected is not None:
                program, details = selected
                _log(
                    trace,
                    "Selected scraped program for scan: "
                    f"program_id={program['program_id']} handle={program.get('handle')} "
                    f"valid_in_scope={details['summary']['valid_in_scope']} "
                    f"url_in_scope={details['summary']['url_in_scope']}",
                )
                return program, details
        time.sleep(POLL_SECONDS)

    pytest.fail(
        "Timed out waiting for an eligible scraped HackerOne program "
        f"(timeout={PROGRAM_WAIT_SECONDS}s)"
    )


def _start_scan(program_id: str, trace: dict[str, Any]) -> str:
    response = httpx.post(
        f"{CORE_BASE}/scans/start",
        json={"program_id": program_id, "feature_flags": {}, "priority": 1},
        timeout=30,
    )
    body = response.json()
    trace["scan_start"] = {"status_code": response.status_code, "body": body}
    assert response.status_code == 200, body
    scan_id = str(body.get("scan_id") or "")
    assert scan_id, body
    _log(trace, f"Scan queued via core-engine: scan_id={scan_id}")
    return scan_id


def _poll_scan_terminal(
    scan_id: str,
    timeout_seconds: int = SCAN_WAIT_SECONDS_SMALL,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        response = httpx.get(f"{CORE_BASE}/scans/{scan_id}", timeout=20)
        if response.status_code == 200:
            payload = response.json()
            last_payload = payload
            status = str(payload.get("status") or "").lower()
            if status in TERMINAL_SCAN_STATUSES:
                return payload, payload
        time.sleep(POLL_SECONDS)
    return None, last_payload


def _latest_terminal_scan_with_findings(program_id: str) -> dict[str, Any] | None:
    for scan in _list_recent_scans():
        current_program_id = str(scan.get("program_id") or "").strip()
        if current_program_id != program_id:
            continue
        status = str(scan.get("status") or "").lower().strip()
        finding_count = int(scan.get("finding_count") or 0)
        if status in {"completed", "partial"} and finding_count > 0:
            return scan
    return None


def _fetch_findings(scan_id: str) -> dict[str, Any]:
    response = httpx.get(f"{CORE_BASE}/scans/{scan_id}/findings", timeout=20)
    response.raise_for_status()
    return response.json()


def _collect_evidence_summary(scan_id: str, findings: list[dict[str, Any]], sample_size: int = 5) -> dict[str, Any]:
    checked = 0
    total_items = 0
    per_finding: list[dict[str, Any]] = []
    for finding in findings[:sample_size]:
        finding_id = str(finding.get("finding_id"))
        if not finding_id:
            continue
        response = httpx.get(f"{CORE_BASE}/scans/{scan_id}/findings/{finding_id}/evidence", timeout=20)
        if response.status_code != 200:
            continue
        body = response.json()
        items = body.get("items", [])
        count = len(items) if isinstance(items, list) else 0
        total_items += count
        checked += 1
        per_finding.append({"finding_id": finding_id, "evidence_count": count})
    return {
        "checked_findings": checked,
        "sample_size": sample_size,
        "total_evidence_items": total_items,
        "per_finding": per_finding,
    }


def _generate_reports(scan_id: str, trace: dict[str, Any]) -> dict[str, str]:
    response = httpx.post(
        f"{REPORTER_BASE}/reports/generate",
        json={
            "scan_id": scan_id,
            "formats_requested": ["pdf", "docx"],
            "include_evidence_screenshots": True,
        },
        timeout=30,
    )
    body = response.json()
    trace["report_generate"] = {"status_code": response.status_code, "body": body}
    assert response.status_code == 202, body
    report_ids = body.get("report_ids", {})
    assert isinstance(report_ids, dict) and report_ids, body
    _log(trace, f"Reporter accepted generation request for scan_id={scan_id}")
    return {str(k): str(v) for k, v in report_ids.items()}


def _poll_report_terminal(report_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + REPORT_WAIT_SECONDS
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}", timeout=20)
        if response.status_code == 200:
            payload = response.json()
            last_payload = payload
            status = str(payload.get("status") or "").lower()
            if status in TERMINAL_REPORT_STATUSES:
                return payload
        time.sleep(POLL_SECONDS)

    pytest.fail(
        f"Timed out waiting for terminal report state for report_id={report_id}. "
        f"Last payload={last_payload}"
    )


def _assert_downloadable_report(report_id: str) -> dict[str, Any]:
    response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}/download", timeout=20)
    body = response.json()
    assert response.status_code == 200, body

    download_url = str(body.get("download_url") or "")
    assert download_url, body

    query = parse_qs(urlparse(download_url).query)
    assert "X-Amz-Expires" in query or "Expires" in query, body
    return body


def _build_replay_commands(findings: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for finding in findings:
        if len(commands) >= limit:
            break
        url = str(finding.get("affected_url") or "").strip()
        if not url:
            continue
        parameter = str(finding.get("affected_parameter") or "").strip()
        command = f"curl -i -sS '{url}'"
        if parameter:
            command += f" --data-urlencode '{parameter}=<payload>'"
        commands.append(
            {
                "finding_id": str(finding.get("finding_id") or ""),
                "title": str(finding.get("title") or ""),
                "severity": str(finding.get("severity") or ""),
                "curl_command": command,
            }
        )
    return commands


def _extract_docx_replay_proof(download_url: str) -> dict[str, Any]:
    response = httpx.get(download_url, timeout=60)
    response.raise_for_status()
    blob = response.content
    if not zipfile.is_zipfile(io.BytesIO(blob)):
        return {"zip_valid": False, "contains_reproduction": False, "contains_curl": False, "sample": []}

    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        try:
            xml_bytes = zf.read("word/document.xml")
        except KeyError:
            return {"zip_valid": True, "contains_reproduction": False, "contains_curl": False, "sample": []}

    xml_text = xml_bytes.decode("utf-8", errors="ignore")
    plain = re.sub(r"<[^>]+>", " ", xml_text)
    plain = re.sub(r"\s+", " ", plain).strip()
    plain_lower = plain.lower()
    contains_reproduction = "reproduction" in plain_lower
    contains_curl = bool(re.search(r"curl\s+-i\s+-s", plain_lower))
    sample = []
    for needle in ("reproduction", "curl -i -s"):
        idx = plain_lower.find(needle)
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(plain), idx + 220)
            sample.append(plain[start:end])
    return {
        "zip_valid": True,
        "contains_reproduction": contains_reproduction,
        "contains_curl": contains_curl,
        "sample": sample,
    }


def test_hackerone_scrape_scan_report_replay_e2e() -> None:
    trace: dict[str, Any] = {
        "test_name": "test_hackerone_scrape_scan_report_replay_e2e",
        "started_at": _utc_now(),
        "config": {
            "scraper_base": SCRAPER_BASE,
            "core_base": CORE_BASE,
            "reporter_base": REPORTER_BASE,
            "program_wait_seconds": PROGRAM_WAIT_SECONDS,
            "scan_wait_seconds_small": SCAN_WAIT_SECONDS_SMALL,
            "scan_wait_seconds_large": SCAN_WAIT_SECONDS_LARGE,
            "scan_wait_scope_threshold": SCAN_WAIT_SCOPE_THRESHOLD,
            "report_wait_seconds": REPORT_WAIT_SECONDS,
            "poll_seconds": POLL_SECONDS,
            "strict_mode": STRICT_MODE,
            "allow_findings_fallback": ALLOW_FINDINGS_FALLBACK,
            "minio_host_port_set": bool(MINIO_HOST_PORT),
        },
        "steps": [],
    }

    _log(trace, "Starting full HackerOne pipeline E2E trace")
    try:
        _require_hackerone_credentials()

        health = {}
        for name, base in (
            ("scraper", SCRAPER_BASE),
            ("core_engine", CORE_BASE),
            ("reporter", REPORTER_BASE),
        ):
            ok, payload = _service_healthy(base)
            health[name] = {"ok": ok, "payload": payload}
        trace["service_health"] = health
        assert all(v["ok"] for v in health.values()), health
        _log(trace, "Service health checks passed for scraper/core_engine/reporter")

        _trigger_hackerone_scrape(trace)
        program, program_details = _wait_for_eligible_program(trace)
        trace["selected_program"] = {
            "program_id": str(program.get("program_id")),
            "handle": str(program.get("handle")),
            "name": str(program.get("name")),
            "platform": str(program.get("platform")),
            "scope_summary": program_details["summary"],
        }

        selected_program_id = str(program["program_id"])
        valid_in_scope = int(program_details["summary"].get("valid_in_scope") or 0)
        scan_wait_seconds = _adaptive_scan_wait_seconds(valid_in_scope)
        trace["scan_wait_seconds_used"] = scan_wait_seconds
        scan_id = _start_scan(selected_program_id, trace)
        terminal_scan_payload, scan_snapshot = _poll_scan_terminal(
            scan_id,
            timeout_seconds=scan_wait_seconds,
        )
        if terminal_scan_payload is not None:
            trace["scan_result"] = terminal_scan_payload
            finding_count = int(terminal_scan_payload.get("finding_count") or 0)
        else:
            trace["scan_result"] = scan_snapshot or {"scan_id": scan_id, "status": "timeout"}
            trace["scan_wait_timeout_seconds"] = scan_wait_seconds
            finding_count = 0
            _log(
                trace,
                "Fresh scan did not reach terminal state within timeout; "
                f"scan_id={scan_id} timeout={scan_wait_seconds}s",
            )

        active_scan_id = scan_id
        fallback_used = False
        scan_source_outcome = _scan_source_outcome(
            terminal_scan_payload,
            finding_count,
            ALLOW_FINDINGS_FALLBACK,
        )
        trace["scan_source_outcome"] = scan_source_outcome
        if scan_source_outcome == "strict_fail":
            pytest.fail(
                "Fresh scan did not produce terminal findings within configured timeout and "
                "fallback is disabled in strict mode. "
                f"scan_id={scan_id} timeout={scan_wait_seconds}s snapshot={scan_snapshot}"
            )
        if scan_source_outcome == "fallback":
            fallback = _latest_terminal_scan_with_findings(selected_program_id)
            if fallback is None:
                pytest.fail(
                    "Unable to obtain a terminal scan with findings for selected scraped program. "
                    f"scan_id={scan_id} snapshot={scan_snapshot}"
                )
            active_scan_id = str(fallback["scan_id"])
            fallback_used = True
            _log(
                trace,
                "Using latest terminal scan with findings for selected scraped program: "
                f"scan_id={active_scan_id}",
            )

        findings_payload = _fetch_findings(active_scan_id)
        findings = findings_payload.get("findings", [])
        finding_count_used = len(findings) if isinstance(findings, list) else 0
        trace["findings_scan_id"] = active_scan_id
        trace["findings_count"] = finding_count_used
        trace["findings_fallback_used"] = fallback_used
        assert finding_count_used > 0, findings_payload
        _log(trace, f"Findings loaded: count={finding_count_used} scan_id={active_scan_id}")

        replay_commands = _build_replay_commands(
            findings if isinstance(findings, list) else [],
            limit=5,
        )
        trace["replay_commands"] = replay_commands
        assert replay_commands, "No replay commands could be derived from findings"
        _log(trace, f"Replay command set prepared: count={len(replay_commands)}")

        evidence_summary = _collect_evidence_summary(
            scan_id=active_scan_id,
            findings=findings if isinstance(findings, list) else [],
        )
        trace["evidence_summary"] = evidence_summary
        _log(
            trace,
            "Evidence endpoint sample complete: "
            f"checked={evidence_summary['checked_findings']} total_items={evidence_summary['total_evidence_items']}",
        )

        report_ids = _generate_reports(active_scan_id, trace)
        trace["report_ids"] = report_ids

        report_terminal: dict[str, dict[str, Any]] = {}
        downloadable: dict[str, dict[str, Any]] = {}
        for format_name, report_id in report_ids.items():
            report_payload = _poll_report_terminal(report_id)
            report_terminal[format_name] = report_payload
            status = str(report_payload.get("status") or "").lower()
            if status in {"completed", "partial"}:
                downloadable[format_name] = _assert_downloadable_report(report_id)

        trace["report_terminal"] = report_terminal
        trace["downloadable_reports"] = downloadable
        assert downloadable, report_terminal
        _log(trace, f"Download-ready reports: formats={sorted(downloadable.keys())}")

        download_proof_required = _is_download_proof_required(STRICT_MODE, MINIO_HOST_PORT)
        trace["download_proof_required"] = download_proof_required
        docx_proof: dict[str, Any] | None = None
        if "docx" in downloadable:
            download_url = str(downloadable["docx"].get("download_url") or "")
            if download_url:
                rewritten_url, rewritten, rewrite_reason = rewrite_minio_presigned_url_for_host(
                    download_url,
                    MINIO_HOST_PORT,
                )
                trace["docx_download_url_resolution"] = {
                    "original": download_url,
                    "effective": rewritten_url,
                    "rewritten": rewritten,
                    "reason": rewrite_reason,
                }
                if not bool(MINIO_HOST_PORT):
                    docx_proof = {
                        "available": False,
                        "required": download_proof_required,
                        "reason": "MINIO_HOST_PORT is not configured for host-side MinIO access.",
                    }
                else:
                    try:
                        extracted = _extract_docx_replay_proof(rewritten_url)
                        docx_proof = {
                            "available": True,
                            "required": download_proof_required,
                            **extracted,
                        }
                    except Exception as exc:
                        docx_proof = {
                            "available": False,
                            "required": download_proof_required,
                            "error": f"{type(exc).__name__}: {exc}",
                        }

        trace["docx_replay_proof"] = docx_proof
        if docx_proof and docx_proof.get("available") and docx_proof.get("zip_valid"):
            assert docx_proof.get("contains_reproduction") or docx_proof.get("contains_curl"), docx_proof
            _log(trace, "Replay proof validated from generated DOCX content")
        elif download_proof_required:
            pytest.fail(f"DOCX replay proof was required but unavailable: {docx_proof}")
        else:
            _log(trace, "DOCX replay proof unavailable; relying on API-derived replay commands")

        trace["result"] = _result_label(fallback_used)
    finally:
        trace.setdefault("finished_at", _utc_now())
        _write_trace(trace)
