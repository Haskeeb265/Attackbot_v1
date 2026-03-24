"""
End-to-end integration trace for the current AttackBot system state.

This test:
1) Ensures the stack is up (docker compose up -d).
2) Enables every scan feature flag currently accepted by scan.jobs schema.
3) Triggers a real scan through Core Engine.
4) Collects process, API, DB, queue, and worker evidence.
5) Writes a root-level markdown report with all observations.

Report output:
    E2E_SYSTEM_FINDINGS.md
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT_DIR / "infra" / "docker-compose.yml"
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE_FILE = ROOT_DIR / ".env.example"
REPORT_PATH = ROOT_DIR / "E2E_SYSTEM_FINDINGS.md"


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _load_env_file_into_process(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded

    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        # Preserve explicit shell env vars; only fill missing keys from .env
        if key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded


LOADED_DOTENV_KEYS = _load_env_file_into_process(ENV_FILE)

CORE_BASE_URL = os.getenv("E2E_CORE_URL", "http://localhost:8002/api/v1")
SCRAPER_BASE_URL = os.getenv("E2E_SCRAPER_URL", "http://localhost:8001/api/v1")
REPORTER_BASE_URL = os.getenv("E2E_REPORTER_URL", "http://localhost:8003/api/v1")
GRAPH_BASE_URL = os.getenv("E2E_GRAPH_URL", "http://localhost:8006/api/v1")
GATEWAY_BASE_URL = os.getenv("E2E_GATEWAY_URL", "http://localhost:8000/api/v1")

RABBITMQ_MGMT_URL = os.getenv("E2E_RABBITMQ_MGMT", "http://localhost:15672/api")
RABBITMQ_USER = os.getenv("E2E_RABBITMQ_USER", "attackbot")
RABBITMQ_PASS = os.getenv("E2E_RABBITMQ_PASS", "attackbot")

DB_DSN = os.getenv("E2E_DB_DSN", "postgresql://attackbot:attackbot@localhost:5432/attackbot")
DB_EXEC_SERVICE = os.getenv("E2E_DB_EXEC_SERVICE", "core-engine")
SCAN_TIMEOUT_SECONDS = int(os.getenv("E2E_SCAN_TIMEOUT_SECONDS", "2400"))
HEALTH_TIMEOUT_SECONDS = int(os.getenv("E2E_HEALTH_TIMEOUT_SECONDS", "300"))
OPTIONAL_HEALTH_TIMEOUT_SECONDS = int(os.getenv("E2E_OPTIONAL_HEALTH_TIMEOUT_SECONDS", "30"))
PROCESS_LOG_TAIL = int(os.getenv("E2E_PROCESS_LOG_TAIL", "300"))
REPORTER_WORKER_LOG_TAIL = int(os.getenv("E2E_REPORTER_WORKER_LOG_TAIL", "300"))
E2E_QUEUE_BASELINE_WAIT_SECONDS = int(
    os.getenv("E2E_QUEUE_BASELINE_WAIT_SECONDS", "300")
)
E2E_QUEUE_BASELINE_POLL_SECONDS = max(
    float(os.getenv("E2E_QUEUE_BASELINE_POLL_SECONDS", "5")),
    1.0,
)
E2E_QUEUE_PURGE_BEFORE_BASELINE = _truthy(
    os.getenv("E2E_QUEUE_PURGE_BEFORE_BASELINE"),
    default=True,
)
E2E_QUEUE_PURGE_SETTLE_SECONDS = int(
    os.getenv("E2E_QUEUE_PURGE_SETTLE_SECONDS", "60")
)
E2E_QUEUE_POST_PURGE_BASELINE_WAIT_SECONDS = int(
    os.getenv("E2E_QUEUE_POST_PURGE_BASELINE_WAIT_SECONDS", "60")
)
E2E_ENFORCE_QUEUE_BASELINE = _truthy(
    os.getenv("E2E_ENFORCE_QUEUE_BASELINE"),
    default=True,
)
E2E_PAUSE_RECONCILER = _truthy(
    os.getenv("E2E_PAUSE_RECONCILER"),
    default=False,
)
LIVE_HACKERONE_ONLY = _truthy(os.getenv("E2E_LIVE_HACKERONE_ONLY"), default=True)
HACKERONE_PROGRAM_WAIT_SECONDS = int(os.getenv("E2E_HACKERONE_PROGRAM_WAIT_SECONDS", "300"))
HACKERONE_PROGRAM_POLL_SECONDS = int(os.getenv("E2E_HACKERONE_PROGRAM_POLL_SECONDS", "10"))
PROGRAM_AUDIT_LIMIT = int(os.getenv("E2E_PROGRAM_AUDIT_LIMIT", "200"))
PINNED_PROGRAM_HANDLE = _env_text(os.getenv("E2E_PINNED_PROGRAM_HANDLE"))
PINNED_PROGRAM_ID = _env_text(os.getenv("E2E_PINNED_PROGRAM_ID"))
ENABLE_FORCED_DEEP_TRACE = _truthy(
    os.getenv("E2E_ENABLE_FORCED_DEEP_TRACE"),
    default=False,
)
DEEP_TRACE_TARGET_URL = os.getenv("E2E_DEEP_TRACE_TARGET_URL", "http://attackbot-e2e-target:3000")
DEEP_TRACE_HOST_CHECK_URL = os.getenv("E2E_DEEP_TRACE_HOST_CHECK_URL", "http://attackbot-e2e-target:3000")
DEEP_TRACE_TARGET_IMAGE = os.getenv("E2E_DEEP_TRACE_TARGET_IMAGE", "bkimminich/juice-shop")
DEEP_TRACE_TARGET_CONTAINER = os.getenv("E2E_DEEP_TRACE_TARGET_CONTAINER", "attackbot-e2e-target")
DEEP_TRACE_STARTUP_TIMEOUT_SECONDS = int(os.getenv("E2E_DEEP_TRACE_STARTUP_TIMEOUT_SECONDS", "240"))
SYNTHETIC_HANDLE_PREFIXES = (
    "e2e-seeded-",
    "m3-seeded-scope-",
    "m3-empty-scope-",
    "deeptrace-",
    "verify-",
)

SERVICE_HEALTH_URLS = {
    "scraper": f"{SCRAPER_BASE_URL}/health",
    "core-engine": f"{CORE_BASE_URL}/health",
    "reporter": f"{REPORTER_BASE_URL}/health",
    "attack-graph-engine": f"{GRAPH_BASE_URL}/health",
    "api-gateway": f"{GATEWAY_BASE_URL}/health",
}
CRITICAL_HEALTH_SERVICES = {"scraper", "core-engine"}

QUEUE_NAMES = [
    "scan.jobs",
    "scan.jobs.dlq",
    "browser.jobs",
    "browser.jobs.dlq",
    "api.fuzz.jobs",
    "api.fuzz.jobs.dlq",
    "js.analysis.jobs",
    "js.analysis.jobs.dlq",
    "scenario.jobs",
    "scenario.jobs.dlq",
    "verify.jobs",
    "verify.jobs.dlq",
    "ai.analysis.jobs",
    "ai.analysis.jobs.dlq",
    "report.jobs",
    "report.jobs.dlq",
    "reports.completed",
]

DB_BRIDGE_SCRIPT = r"""
import asyncio
import json
import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal

import asyncpg


def _normalize_dsn(raw: str) -> str:
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql://" + raw[len("postgresql+asyncpg://"):]
    return raw


def _coerce_arg(value):
    if isinstance(value, dict):
        tag = value.get("__type")
        if tag == "datetime":
            return datetime.fromisoformat(value["value"])
        if tag == "uuid":
            return uuid.UUID(value["value"])
    return value


def _serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, tuple):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    return value


async def main():
    payload = json.loads(sys.argv[1])
    op = payload["op"]
    query = payload["query"]
    args = [_coerce_arg(v) for v in payload.get("args", [])]

    dsn = _normalize_dsn(os.environ.get("DATABASE_URL", ""))
    if not dsn:
        print(json.dumps({"ok": False, "error": "DATABASE_URL missing in container env"}))
        raise SystemExit(2)

    try:
        conn = await asyncpg.connect(dsn)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}))
        raise SystemExit(2)

    try:
        if op == "fetchrow":
            row = await conn.fetchrow(query, *args)
            result = dict(row) if row else None
        elif op == "fetch":
            rows = await conn.fetch(query, *args)
            result = [dict(r) for r in rows]
        elif op == "execute":
            result = await conn.execute(query, *args)
        else:
            raise ValueError(f"Unsupported op: {op}")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}))
        raise SystemExit(2)
    finally:
        await conn.close()

    print(json.dumps({"ok": True, "result": _serialize(result)}))


asyncio.run(main())
""".strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim(text: str, limit: int = 20000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated]"


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return value


def _record_to_dict(record: Any) -> dict[str, Any]:
    return {k: _json_safe(v) for k, v in dict(record).items()}


def _log_step(obs: dict[str, Any], message: str) -> None:
    obs["steps"].append(f"{_utc_now()} | {message}")


def _compose_cmd(*parts: str) -> list[str]:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)]
    if ENV_FILE.exists():
        cmd.extend(["--env-file", str(ENV_FILE)])
    cmd.extend(parts)
    return cmd


def _run_command(
    args: list[str],
    timeout: int = 120,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(ROOT_DIR),
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _record_command(
    obs: dict[str, Any],
    label: str,
    args: list[str],
    result: subprocess.CompletedProcess[str],
) -> None:
    obs["commands"].append(
        {
            "label": label,
            "cmd": " ".join(args),
            "returncode": result.returncode,
            "stdout": _trim(result.stdout),
            "stderr": _trim(result.stderr),
        }
    )


def _docker_available() -> bool:
    try:
        result = _run_command(["docker", "info"], timeout=30)
        return result.returncode == 0
    except Exception:
        return False


def _ensure_env_file(obs: dict[str, Any]) -> None:
    if ENV_FILE.exists():
        loaded = _load_env_file_into_process(ENV_FILE)
        _log_step(
            obs,
            f".env present (loaded {len(loaded)} missing keys into process env)",
        )
        return
    if ENV_EXAMPLE_FILE.exists():
        shutil.copyfile(ENV_EXAMPLE_FILE, ENV_FILE)
        loaded = _load_env_file_into_process(ENV_FILE)
        _log_step(
            obs,
            f".env missing; copied from .env.example (loaded {len(loaded)} keys)",
        )
        return
    _log_step(obs, ".env missing and .env.example missing")


async def _wait_for_health(url: str, timeout_seconds: int) -> dict[str, Any]:
    start = datetime.now(timezone.utc)
    last: dict[str, Any] = {"status_code": None, "body": None, "error": None}
    while True:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        if elapsed > timeout_seconds:
            return last
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
            payload: Any
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            last = {"status_code": resp.status_code, "body": payload, "error": None}
            if resp.status_code == 200:
                return last
        except Exception as exc:  # pragma: no cover - best effort
            last = {"status_code": None, "body": None, "error": str(exc)}
        await _async_sleep(2)


async def _async_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)


async def _collect_service_health(obs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for service, url in SERVICE_HEALTH_URLS.items():
        timeout = (
            HEALTH_TIMEOUT_SECONDS
            if service in CRITICAL_HEALTH_SERVICES
            else OPTIONAL_HEALTH_TIMEOUT_SECONDS
        )
        results[service] = await _wait_for_health(url, timeout)
        _log_step(
            obs,
            f"Health probe {service}: status_code={results[service]['status_code']}",
        )
    return results


def _parse_last_json_line(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _encode_db_arg(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"__type": "datetime", "value": value.isoformat()}
    if isinstance(value, uuid.UUID):
        return {"__type": "uuid", "value": str(value)}
    if isinstance(value, list):
        return [_encode_db_arg(v) for v in value]
    if isinstance(value, tuple):
        return [_encode_db_arg(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _encode_db_arg(v) for k, v in value.items()}
    return value


class _DockerExecDbConnection:
    def __init__(self, service: str):
        self.service = service

    async def _call(self, op: str, query: str, *args: Any) -> Any:
        payload = {
            "op": op,
            "query": query,
            "args": [_encode_db_arg(a) for a in args],
        }
        cmd = _compose_cmd(
            "exec",
            "-T",
            self.service,
            "python",
            "-c",
            DB_BRIDGE_SCRIPT,
            json.dumps(payload),
        )
        result = await asyncio.to_thread(_run_command, cmd, 240)
        output = _parse_last_json_line(result.stdout)
        if output is None:
            raise RuntimeError(
                "Failed to parse DB bridge output. "
                f"rc={result.returncode} stdout={_trim(result.stdout[-2000:])} "
                f"stderr={_trim(result.stderr[-2000:])}"
            )
        if not output.get("ok"):
            raise RuntimeError(
                f"DB bridge operation failed: {output.get('error')} "
                f"({output.get('error_type', 'unknown')})"
            )
        return output.get("result")

    async def fetchrow(self, query: str, *args: Any) -> Any:
        return await self._call("fetchrow", query, *args)

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        result = await self._call("fetch", query, *args)
        return result or []

    async def execute(self, query: str, *args: Any) -> Any:
        return await self._call("execute", query, *args)

    async def close(self) -> None:
        return None

    async def healthcheck(self) -> dict[str, Any]:
        row = await self.fetchrow(
            "SELECT current_database() AS db_name, current_user AS db_user, version() AS version"
        )
        return row or {}


async def _looks_like_attackbot_schema(conn: Any) -> bool:
    try:
        program_cols = await conn.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'programs'
            """
        )
        scan_cols = await conn.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'scans'
            """
        )
    except Exception:
        return False

    program_col_set = {str(r["column_name"]) for r in program_cols}
    scan_col_set = {str(r["column_name"]) for r in scan_cols}
    required_program_cols = {"program_id", "handle"}
    required_scan_cols = {"scan_id", "program_id", "status"}
    return required_program_cols.issubset(program_col_set) and required_scan_cols.issubset(
        scan_col_set
    )


async def _get_db_connection() -> tuple[Any, str]:
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg is required for end-to-end integration trace")

    direct_error = ""
    try:
        conn = await asyncpg.connect(DB_DSN)
        if await _looks_like_attackbot_schema(conn):
            return conn, f"direct-asyncpg ({DB_DSN})"
        await conn.close()
        direct_error = (
            f"Direct DB at {DB_DSN} does not match expected AttackBot schema; "
            "falling back to docker-exec DB bridge."
        )
    except Exception as exc:
        direct_error = (
            f"Direct DB connection failed for {DB_DSN}: {exc}; "
            "falling back to docker-exec DB bridge."
        )

    bridge = _DockerExecDbConnection(DB_EXEC_SERVICE)
    try:
        health = await bridge.healthcheck()
    except Exception as exc:
        raise RuntimeError(
            f"{direct_error} DB bridge via service '{DB_EXEC_SERVICE}' failed: {exc}"
        ) from exc

    version = str(health.get("version", "unknown-version"))
    return bridge, f"docker-exec ({DB_EXEC_SERVICE}) | {version}"


async def _list_program_inventory(conn: Any, limit: int = 200) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT
            p.program_id,
            p.handle,
            p.name,
            p.platform,
            p.is_active,
            p.updated_at,
            p.created_at,
            COUNT(*) FILTER (
                WHERE s.scope_type = 'in_scope'
            )::int AS in_scope_count,
            COUNT(*) FILTER (
                WHERE s.scope_type = 'in_scope'
                  AND COALESCE(TRIM(s.value), '') <> ''
            )::int AS valid_in_scope_count,
            COUNT(*) FILTER (
                WHERE s.scope_type = 'out_of_scope'
            )::int AS out_of_scope_count
        FROM programs p
        LEFT JOIN program_scopes s ON s.program_id = p.program_id
        GROUP BY
            p.program_id, p.handle, p.name, p.platform, p.is_active, p.updated_at, p.created_at
        ORDER BY p.updated_at DESC NULLS LAST, p.created_at DESC
        LIMIT $1::int
        """,
        limit,
    )

    inventory: list[dict[str, Any]] = []
    for row in rows:
        data = _record_to_dict(row)
        data["program_id"] = str(data.get("program_id"))
        data["handle"] = str(data.get("handle") or "")
        data["platform"] = str(data.get("platform") or "")
        data["name"] = str(data.get("name") or "")
        data["in_scope_count"] = int(data.get("in_scope_count") or 0)
        data["valid_in_scope_count"] = int(data.get("valid_in_scope_count") or 0)
        data["out_of_scope_count"] = int(data.get("out_of_scope_count") or 0)
        inventory.append(data)
    return inventory


def _is_hackerone_eligible(program: dict[str, Any]) -> bool:
    platform = str(program.get("platform") or "").strip().lower()
    is_active = program.get("is_active")
    valid_in_scope_count = int(program.get("valid_in_scope_count") or 0)
    return (
        platform == "hackerone"
        and is_active is not False
        and valid_in_scope_count > 0
        and not _is_synthetic_program(program)
    )


def _is_synthetic_program(program: dict[str, Any]) -> bool:
    handle = str(program.get("handle") or "").strip().lower()
    if any(handle.startswith(prefix) for prefix in SYNTHETIC_HANDLE_PREFIXES):
        return True
    return False


def _build_program_selection_audit(
    inventory: list[dict[str, Any]],
    selected_program_id: str | None,
    selection_policy: str = "most_recent_eligible_hackerone",
) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for program in inventory:
        program_id = str(program.get("program_id"))
        reasons: list[str] = []
        if str(program.get("platform") or "").strip().lower() != "hackerone":
            reasons.append("platform is not hackerone")
        if int(program.get("valid_in_scope_count") or 0) <= 0:
            reasons.append("no non-empty in_scope scope entries")
        if program.get("is_active") is False:
            reasons.append("program is inactive")
        if _is_synthetic_program(program):
            reasons.append("synthetic/test program handle excluded in live mode")

        eligible = len(reasons) == 0
        selected = selected_program_id == program_id
        if selected:
            if selection_policy == "pinned_program_id":
                reason = (
                    "selected: matched E2E_PINNED_PROGRAM_ID="
                    f"{PINNED_PROGRAM_ID}"
                )
            elif selection_policy == "pinned_program_handle":
                reason = (
                    "selected: matched E2E_PINNED_PROGRAM_HANDLE="
                    f"{PINNED_PROGRAM_HANDLE}"
                )
            elif selection_policy == "pinned_program_id_and_handle":
                reason = (
                    "selected: matched both pinned selectors "
                    f"(id={PINNED_PROGRAM_ID}, handle={PINNED_PROGRAM_HANDLE})"
                )
            else:
                reason = "selected: most recently updated eligible HackerOne program"
        elif eligible:
            if selection_policy.startswith("pinned_"):
                reason = "not selected: run pinned to explicit program selector(s)"
            else:
                reason = "not selected: single-program live e2e chooses most recent eligible program"
        else:
            reason = "; ".join(reasons)

        audit.append(
            {
                **program,
                "eligible_for_live_hackerone_scan": eligible,
                "selected_for_this_run": selected,
                "selection_reason": reason,
            }
        )
    return audit


def _find_program_by_pinned_selector(
    inventory: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    pinned_id = str(PINNED_PROGRAM_ID or "").strip()
    pinned_handle = str(PINNED_PROGRAM_HANDLE or "").strip().lower()

    if pinned_id and pinned_handle:
        for program in inventory:
            if (
                str(program.get("program_id")) == pinned_id
                and str(program.get("handle") or "").strip().lower() == pinned_handle
            ):
                return program, "pinned_program_id_and_handle"
        return None, "pinned_program_id_and_handle"

    if pinned_id:
        for program in inventory:
            if str(program.get("program_id")) == pinned_id:
                return program, "pinned_program_id"
        return None, "pinned_program_id"

    if pinned_handle:
        for program in inventory:
            if str(program.get("handle") or "").strip().lower() == pinned_handle:
                return program, "pinned_program_handle"
        return None, "pinned_program_handle"

    return None, None


async def _select_live_hackerone_program(
    conn: Any,
    obs: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    started = datetime.now(timezone.utc)
    last_total = -1
    last_eligible = -1

    while True:
        inventory = await _list_program_inventory(conn, PROGRAM_AUDIT_LIMIT)
        pinned_selected, pinned_policy = _find_program_by_pinned_selector(inventory)
        if pinned_policy is not None:
            selected_id = str(pinned_selected["program_id"]) if pinned_selected else None
            audit = _build_program_selection_audit(
                inventory,
                selected_id,
                selection_policy=pinned_policy,
            )
            if pinned_selected:
                return pinned_selected, audit, pinned_policy

            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            if elapsed > HACKERONE_PROGRAM_WAIT_SECONDS:
                return None, audit, pinned_policy
            await _async_sleep(HACKERONE_PROGRAM_POLL_SECONDS)
            continue

        eligible = [p for p in inventory if _is_hackerone_eligible(p)]
        if len(inventory) != last_total or len(eligible) != last_eligible:
            _log_step(
                obs,
                "Program inventory snapshot: "
                f"total={len(inventory)} eligible_hackerone_with_scope={len(eligible)}",
            )
            last_total = len(inventory)
            last_eligible = len(eligible)

        selected = eligible[0] if eligible else None
        selected_id = str(selected["program_id"]) if selected else None
        audit = _build_program_selection_audit(inventory, selected_id)
        if selected:
            return selected, audit, "most_recent_eligible_hackerone"

        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed > HACKERONE_PROGRAM_WAIT_SECONDS:
            return None, audit, "most_recent_eligible_hackerone"
        await _async_sleep(HACKERONE_PROGRAM_POLL_SECONDS)


async def _fetch_program_scope(conn: Any, program_id: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT scope_type, asset_type, value, notes
        FROM program_scopes
        WHERE program_id = $1::uuid
        ORDER BY scope_type, value
        """,
        program_id,
    )
    return [_record_to_dict(row) for row in rows]


def _all_feature_flags_enabled() -> dict[str, bool]:
    return {
        "asset_discovery": True,
        "fingerprinting": True,
        "enumeration": True,
        "nuclei": True,
        "xss": True,
        "cors": True,
        "secret_js": True,
        "browser_session": True,
        "api_fuzzing": True,
        "crlf": True,
        "sqli": True,
        "ssrf": True,
        "takeover": True,
        "secret_repo": True,
        "scenario_runner": True,
        "ai_hypothesis": True,
        "idor_verification": True,
    }


async def _start_scan(program_id: str, feature_flags: dict[str, bool]) -> httpx.Response:
    payload = {
        "program_id": program_id,
        "priority": 1,
        "feature_flags": feature_flags,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        return await client.post(f"{CORE_BASE_URL}/scans/start", json=payload)


async def _wait_for_terminal_scan(
    conn: Any,
    program_id: str,
    created_after: datetime,
    timeout_seconds: int,
    obs: dict[str, Any],
) -> dict[str, Any]:
    import asyncio

    started = datetime.now(timezone.utc)
    last_status: str | None = None

    while True:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed > timeout_seconds:
            raise AssertionError(
                f"Timed out waiting for terminal scan status after {timeout_seconds}s"
            )

        row = await conn.fetchrow(
            """
            SELECT scan_id, program_id, status, finding_count, severity_breakdown,
                   retry_count, partial_detail, error_detail,
                   started_at, completed_at, created_at
            FROM scans
            WHERE program_id = $1::uuid
              AND created_at >= $2::timestamptz
            ORDER BY created_at DESC
            LIMIT 1
            """,
            program_id,
            created_after,
        )

        if row:
            status = str(row["status"])
            if status != last_status:
                last_status = status
                _log_step(obs, f"Scan status transition observed: {status}")
            if status in {"completed", "partial", "failed_scope", "failed_internal"}:
                return _record_to_dict(row)
        await asyncio.sleep(3)


async def _fetch_latest_scan_for_program(
    conn: Any,
    program_id: str,
    created_after: datetime | None = None,
) -> dict[str, Any] | None:
    if created_after is None:
        row = await conn.fetchrow(
            """
            SELECT scan_id, program_id, status, finding_count, severity_breakdown,
                   retry_count, partial_detail, error_detail,
                   started_at, completed_at, created_at
            FROM scans
            WHERE program_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            program_id,
        )
    else:
        row = await conn.fetchrow(
            """
            SELECT scan_id, program_id, status, finding_count, severity_breakdown,
                   retry_count, partial_detail, error_detail,
                   started_at, completed_at, created_at
            FROM scans
            WHERE program_id = $1::uuid
              AND created_at >= $2::timestamptz
            ORDER BY created_at DESC
            LIMIT 1
            """,
            program_id,
            created_after,
        )
    return _record_to_dict(row) if row else None


async def _collect_scan_data(conn: Any, scan_id: str) -> dict[str, Any]:
    scan_row = await conn.fetchrow(
        """
        SELECT scan_id, program_id, status, finding_count, severity_breakdown,
               retry_count, partial_detail, error_detail,
               started_at, completed_at, created_at
        FROM scans
        WHERE scan_id = $1::uuid
        """,
        scan_id,
    )

    stage_rows = await conn.fetch(
        """
        SELECT stage_number, stage_name, status, started_at, completed_at,
               error_detail, output_summary
        FROM scan_stages
        WHERE scan_id = $1::uuid
        ORDER BY stage_number ASC, started_at ASC
        """,
        scan_id,
    )

    findings = await conn.fetch(
        """
        SELECT finding_id, vulnerability_type, title, severity, cvss_score,
               affected_url, affected_parameter, is_verified, is_false_positive,
               source, created_at
        FROM findings
        WHERE scan_id = $1::uuid
        ORDER BY cvss_score DESC NULLS LAST, created_at ASC
        """,
        scan_id,
    )

    counts = await conn.fetchrow(
        """
        SELECT
            (SELECT COUNT(*)::int FROM assets WHERE scan_id = $1::uuid) AS assets_count,
            (SELECT COUNT(*)::int FROM endpoints WHERE scan_id = $1::uuid) AS endpoints_count,
            (SELECT COUNT(*)::int FROM js_assets WHERE scan_id = $1::uuid) AS js_assets_count,
            (SELECT COUNT(*)::int FROM findings WHERE scan_id = $1::uuid) AS findings_count,
            (SELECT COUNT(*)::int FROM finding_evidence fe
                JOIN findings f ON fe.finding_id = f.finding_id
                WHERE f.scan_id = $1::uuid) AS evidence_count
        """,
        scan_id,
    )

    severity_breakdown_rows = await conn.fetch(
        """
        SELECT severity, COUNT(*)::int AS count
        FROM findings
        WHERE scan_id = $1::uuid
        GROUP BY severity
        ORDER BY severity
        """,
        scan_id,
    )

    source_breakdown_rows = await conn.fetch(
        """
        SELECT COALESCE(source, 'unknown') AS source, COUNT(*)::int AS count
        FROM findings
        WHERE scan_id = $1::uuid
        GROUP BY source
        ORDER BY count DESC, source ASC
        """,
        scan_id,
    )

    return {
        "scan_row": _record_to_dict(scan_row) if scan_row else None,
        "scan_stages": [_record_to_dict(r) for r in stage_rows],
        "findings": [_record_to_dict(r) for r in findings],
        "artifact_counts": _record_to_dict(counts) if counts else {},
        "severity_breakdown_rows": [_record_to_dict(r) for r in severity_breakdown_rows],
        "source_breakdown_rows": [_record_to_dict(r) for r in source_breakdown_rows],
    }


async def _safe_get_json(url: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
        payload: Any
        try:
            payload = resp.json()
        except Exception:
            payload = resp.text
        return {
            "url": url,
            "status_code": resp.status_code,
            "payload": _json_safe(payload),
        }
    except Exception as exc:
        return {"url": url, "status_code": None, "error": str(exc), "payload": None}


async def _collect_rabbitmq_queue_states() -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=15) as client:
        for queue_name in QUEUE_NAMES:
            url = f"{RABBITMQ_MGMT_URL}/queues/%2F/{queue_name}"
            try:
                resp = await client.get(url, auth=(RABBITMQ_USER, RABBITMQ_PASS))
                if resp.status_code == 200:
                    payload = resp.json()
                    states.append(
                        {
                            "queue": queue_name,
                            "exists": True,
                            "messages": payload.get("messages"),
                            "messages_ready": payload.get("messages_ready"),
                            "messages_unacknowledged": payload.get(
                                "messages_unacknowledged"
                            ),
                            "consumers": payload.get("consumers"),
                        }
                    )
                else:
                    states.append(
                        {
                            "queue": queue_name,
                            "exists": False,
                            "status_code": resp.status_code,
                            "messages": None,
                            "consumers": None,
                        }
                    )
            except Exception as exc:
                states.append(
                    {
                        "queue": queue_name,
                        "exists": False,
                        "status_code": None,
                        "messages": None,
                        "consumers": None,
                        "error": str(exc),
                    }
                )
    return states


async def _fetch_rabbitmq_queue_state(queue_name: str) -> dict[str, Any]:
    url = f"{RABBITMQ_MGMT_URL}/queues/%2F/{queue_name}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, auth=(RABBITMQ_USER, RABBITMQ_PASS))
        if resp.status_code != 200:
            return {
                "queue": queue_name,
                "exists": False,
                "status_code": resp.status_code,
                "messages": None,
                "messages_ready": None,
                "messages_unacknowledged": None,
                "consumers": None,
            }
        payload = resp.json()
        return {
            "queue": queue_name,
            "exists": True,
            "status_code": resp.status_code,
            "messages": payload.get("messages"),
            "messages_ready": payload.get("messages_ready"),
            "messages_unacknowledged": payload.get("messages_unacknowledged"),
            "consumers": payload.get("consumers"),
        }
    except Exception as exc:
        return {
            "queue": queue_name,
            "exists": False,
            "status_code": None,
            "messages": None,
            "messages_ready": None,
            "messages_unacknowledged": None,
            "consumers": None,
            "error": str(exc),
        }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


async def _purge_rabbitmq_queue(queue_name: str) -> dict[str, Any]:
    before = await _fetch_rabbitmq_queue_state(queue_name)
    before_ready = _safe_int(before.get("messages_ready"), 0)
    before_unacked = _safe_int(before.get("messages_unacknowledged"), 0)

    purge_url = f"{RABBITMQ_MGMT_URL}/queues/%2F/{queue_name}/contents"
    purge_status: int | None = None
    purge_error: str | None = None

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.delete(purge_url, auth=(RABBITMQ_USER, RABBITMQ_PASS))
        purge_status = resp.status_code
    except Exception as exc:
        purge_error = str(exc)

    after = await _fetch_rabbitmq_queue_state(queue_name)
    after_ready = _safe_int(after.get("messages_ready"), 0)
    after_unacked = _safe_int(after.get("messages_unacknowledged"), 0)

    ok = purge_error is None and purge_status in {204, 200}
    return {
        "queue": queue_name,
        "ok": ok,
        "purge_status_code": purge_status,
        "purge_error": purge_error,
        "state_before": before,
        "state_after": after,
        "ready_before": before_ready,
        "ready_after": after_ready,
        "unacked_before": before_unacked,
        "unacked_after": after_unacked,
    }


async def _purge_scan_jobs_for_baseline(obs: dict[str, Any]) -> dict[str, Any]:
    """
    Actively clear pre-existing ready jobs from scan.jobs before baseline polling.
    This is used for E2E isolation when queue baseline enforcement is enabled.
    """
    enabled = E2E_ENFORCE_QUEUE_BASELINE and E2E_QUEUE_PURGE_BEFORE_BASELINE
    result: dict[str, Any] = {
        "enabled": enabled,
        "queue": "scan.jobs",
        "settle_timeout_seconds": E2E_QUEUE_PURGE_SETTLE_SECONDS,
        "settle_poll_seconds": E2E_QUEUE_BASELINE_POLL_SECONDS,
        "attempts": [],
        "initial_state": {},
        "settle_state": {},
        "final_state": {},
        "settled_unacked": None,
        "ok": True,
    }
    if not enabled:
        result["note"] = "queue purge disabled for this run"
        return result

    initial_state = await _fetch_rabbitmq_queue_state("scan.jobs")
    result["initial_state"] = initial_state
    _log_step(
        obs,
        "Queue purge pre-check scan.jobs: "
        f"ready={initial_state.get('messages_ready')} "
        f"unacked={initial_state.get('messages_unacknowledged')} "
        f"consumers={initial_state.get('consumers')}",
    )

    first_attempt = await _purge_rabbitmq_queue("scan.jobs")
    result["attempts"].append(first_attempt)
    _log_step(
        obs,
        "Queue purge attempt #1 scan.jobs: "
        f"ok={first_attempt.get('ok')} "
        f"status={first_attempt.get('purge_status_code')} "
        f"ready_before={first_attempt.get('ready_before')} "
        f"ready_after={first_attempt.get('ready_after')}",
    )
    if first_attempt.get("purge_error"):
        result["ok"] = False
        result["error"] = first_attempt.get("purge_error")
        result["final_state"] = first_attempt.get("state_after") or {}
        return result

    settle_started = datetime.now(timezone.utc)
    last_snapshot: dict[str, Any] = first_attempt.get("state_after") or {}
    settled_unacked = False
    while True:
        elapsed = (datetime.now(timezone.utc) - settle_started).total_seconds()
        current = await _fetch_rabbitmq_queue_state("scan.jobs")
        last_snapshot = current
        unacked_now = _safe_int(current.get("messages_unacknowledged"), 0)
        if unacked_now == 0:
            settled_unacked = True
            break
        if elapsed >= E2E_QUEUE_PURGE_SETTLE_SECONDS:
            break
        await _async_sleep(E2E_QUEUE_BASELINE_POLL_SECONDS)

    result["settled_unacked"] = settled_unacked
    result["settle_state"] = last_snapshot
    _log_step(
        obs,
        "Queue purge settle window scan.jobs: "
        f"settled_unacked={settled_unacked} "
        f"ready={last_snapshot.get('messages_ready')} "
        f"unacked={last_snapshot.get('messages_unacknowledged')}",
    )

    second_attempt = await _purge_rabbitmq_queue("scan.jobs")
    result["attempts"].append(second_attempt)
    _log_step(
        obs,
        "Queue purge attempt #2 scan.jobs: "
        f"ok={second_attempt.get('ok')} "
        f"status={second_attempt.get('purge_status_code')} "
        f"ready_before={second_attempt.get('ready_before')} "
        f"ready_after={second_attempt.get('ready_after')}",
    )
    if second_attempt.get("purge_error"):
        result["ok"] = False
        result["error"] = second_attempt.get("purge_error")

    result["final_state"] = second_attempt.get("state_after") or {}
    if _safe_int(result["final_state"].get("messages_ready"), 0) != 0:
        result["ok"] = False
        result["error"] = (
            "scan.jobs still has ready messages after purge attempts: "
            f"{result['final_state'].get('messages_ready')}"
        )
    return result


async def _wait_for_scan_jobs_queue_baseline(
    obs: dict[str, Any],
    timeout_seconds: int,
    poll_seconds: float,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    last_ready: int | None = None
    last_state: dict[str, Any] = {
        "queue": "scan.jobs",
        "exists": False,
        "messages": None,
        "messages_ready": None,
        "messages_unacknowledged": None,
        "consumers": None,
    }

    while True:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed > timeout_seconds:
            return {
                "reached": False,
                "timeout_seconds": timeout_seconds,
                "seconds_waited": round(elapsed, 2),
                "state": last_state,
            }

        state = await _fetch_rabbitmq_queue_state("scan.jobs")
        last_state = state

        try:
            ready = int(state.get("messages_ready") or 0)
        except Exception:
            ready = None

        if ready != last_ready:
            _log_step(
                obs,
                "Queue baseline poll scan.jobs: "
                f"ready={state.get('messages_ready')} "
                f"unacked={state.get('messages_unacknowledged')} "
                f"consumers={state.get('consumers')}",
            )
            last_ready = ready

        if ready == 0:
            return {
                "reached": True,
                "timeout_seconds": timeout_seconds,
                "seconds_waited": round(elapsed, 2),
                "state": state,
            }

        await _async_sleep(poll_seconds)


async def _wait_for_http_up(url: str, timeout_seconds: int = 180) -> bool:
    started = datetime.now(timezone.utc)
    while True:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed > timeout_seconds:
            return False
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(url)
            if resp.status_code < 500:
                return True
        except Exception:
            pass
        await _async_sleep(2)


def _discover_core_worker_network(obs: dict[str, Any]) -> str | None:
    container_id_cmd = _compose_cmd("ps", "-q", "core-worker")
    container_id_result = _run_command(container_id_cmd, timeout=30)
    _record_command(obs, "docker compose ps -q core-worker", container_id_cmd, container_id_result)
    if container_id_result.returncode != 0:
        return None

    container_id = container_id_result.stdout.strip()
    if not container_id:
        return None

    inspect_cmd = [
        "docker",
        "inspect",
        container_id,
        "--format",
        "{{json .NetworkSettings.Networks}}",
    ]
    inspect_result = _run_command(inspect_cmd, timeout=30)
    _record_command(obs, "docker inspect core-worker networks", inspect_cmd, inspect_result)
    if inspect_result.returncode != 0:
        return None

    raw = inspect_result.stdout.strip()
    if not raw:
        return None

    try:
        networks = json.loads(raw)
    except Exception:
        return None
    if not isinstance(networks, dict) or not networks:
        return None

    return sorted(networks.keys())[0]


def _is_container_on_network(container: str, network: str) -> bool:
    cmd = [
        "docker",
        "inspect",
        container,
        "--format",
        "{{json .NetworkSettings.Networks}}",
    ]
    result = _run_command(cmd, timeout=30)
    if result.returncode != 0:
        return False
    raw = result.stdout.strip()
    if not raw:
        return False
    try:
        networks = json.loads(raw)
    except Exception:
        return False
    return isinstance(networks, dict) and network in networks


def _core_worker_can_reach_http(url: str) -> bool:
    script = (
        "import sys, urllib.request\n"
        "url = sys.argv[1]\n"
        "try:\n"
        "    resp = urllib.request.urlopen(url, timeout=8)\n"
        "    status = getattr(resp, 'status', 200)\n"
        "    raise SystemExit(0 if status < 500 else 1)\n"
        "except Exception:\n"
        "    raise SystemExit(2)\n"
    )
    cmd = _compose_cmd("exec", "-T", "core-worker", "python", "-c", script, url)
    result = _run_command(cmd, timeout=20)
    return result.returncode == 0


async def _wait_for_http_up_from_core_worker(url: str, timeout_seconds: int = 180) -> bool:
    started = datetime.now(timezone.utc)
    while True:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed > timeout_seconds:
            return False
        if _core_worker_can_reach_http(url):
            return True
        await _async_sleep(2)


async def _ensure_deep_trace_target(obs: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "attempted": True,
        "container": DEEP_TRACE_TARGET_CONTAINER,
        "image": DEEP_TRACE_TARGET_IMAGE,
        "target_url": DEEP_TRACE_TARGET_URL,
        "host_check_url": DEEP_TRACE_HOST_CHECK_URL,
    }

    # If caller supplied a custom target URL, do not force-start Juice Shop.
    custom_target = (
        "E2E_DEEP_TRACE_TARGET_URL" in os.environ
        or "E2E_DEEP_TRACE_HOST_CHECK_URL" in os.environ
    )
    if custom_target:
        probe_url = DEEP_TRACE_HOST_CHECK_URL or DEEP_TRACE_TARGET_URL
        ready = await _wait_for_http_up_from_core_worker(
            probe_url,
            timeout_seconds=DEEP_TRACE_STARTUP_TIMEOUT_SECONDS,
        )
        result["ready"] = ready
        result["started_container"] = False
        result["network"] = None
        return result

    core_worker_network = _discover_core_worker_network(obs)
    result["network"] = core_worker_network
    if not core_worker_network:
        result["ready"] = False
        result["started_container"] = False
        result["error"] = "Could not discover core-worker Docker network"
        return result

    check_cmd = [
        "docker",
        "ps",
        "--filter",
        f"name={DEEP_TRACE_TARGET_CONTAINER}",
        "--format",
        "{{.Names}}",
    ]
    check_result = _run_command(check_cmd, timeout=30)
    _record_command(obs, "docker ps deep-trace target", check_cmd, check_result)
    running = DEEP_TRACE_TARGET_CONTAINER in check_result.stdout

    if not running:
        rm_cmd = ["docker", "rm", "-f", DEEP_TRACE_TARGET_CONTAINER]
        rm_result = _run_command(rm_cmd, timeout=30)
        _record_command(obs, "docker rm deep-trace target (best-effort)", rm_cmd, rm_result)

        run_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            DEEP_TRACE_TARGET_CONTAINER,
            "--network",
            core_worker_network,
            DEEP_TRACE_TARGET_IMAGE,
        ]
        run_result = _run_command(run_cmd, timeout=120)
        _record_command(obs, "docker run deep-trace target", run_cmd, run_result)
        result["started_container"] = run_result.returncode == 0
    else:
        result["started_container"] = False
        if not _is_container_on_network(DEEP_TRACE_TARGET_CONTAINER, core_worker_network):
            connect_cmd = ["docker", "network", "connect", core_worker_network, DEEP_TRACE_TARGET_CONTAINER]
            connect_result = _run_command(connect_cmd, timeout=30)
            _record_command(obs, "docker network connect deep-trace target", connect_cmd, connect_result)
            result["connected_network"] = connect_result.returncode == 0
        else:
            result["connected_network"] = True

    ready = await _wait_for_http_up_from_core_worker(
        DEEP_TRACE_TARGET_URL,
        timeout_seconds=DEEP_TRACE_STARTUP_TIMEOUT_SECONDS,
    )
    result["ready"] = ready
    return result


def _parse_diag_json(stdout: str) -> dict[str, Any] | None:
    marker = "E2E_DIAG_JSON_START:"
    idx = stdout.rfind(marker)
    if idx == -1:
        return None
    raw = stdout[idx + len(marker):].strip()
    try:
        return json.loads(raw)
    except Exception:
        return None


def _build_deep_trace_script(target_url: str) -> str:
    # Keep this script self-contained; it executes inside core-worker container.
    return f"""
import asyncio
import json
import subprocess
import time
import traceback
import urllib.request

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.pipeline import (
    enumeration,
    fingerprinting,
    js_secrets,
    nuclei_scan,
    web_vuln_tests,
)
from backend.services.core_engine.pipeline.context import FeatureFlags, ScanContext, ScopeDefinition
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.storage import init_storage

TARGET = {json.dumps(target_url)}

async def main():
    out = {{
        "target_url": TARGET,
        "started_at": time.time(),
        "stages": [],
        "summary": {{}},
        "feature_flags_used": {{}},
        "fatal_error": None,
        "traceback": None,
    }}

    def record(name, status, started, **details):
        out["stages"].append({{
            "name": name,
            "status": status,
            "duration_seconds": round(time.time() - started, 3),
            "details": details,
        }})

    try:
        cfg = EngineConfig()
        cfg.httpx_timeout = 120
        cfg.ffuf_timeout = 120
        cfg.waybackurls_timeout = 90
        cfg.nuclei_timeout = 120
        cfg.nuclei_rate_limit = 25
        cfg.nuclei_bulk_size = 10
        cfg.nuclei_concurrency = 10

        init_storage(
            endpoint=cfg.minio_endpoint,
            access_key=cfg.minio_access_key,
            secret_key=cfg.minio_secret_key,
            secure=cfg.minio_secure,
        )

        desired_flags = {{
            "asset_discovery": True,
            "fingerprinting": True,
            "enumeration": True,
            "nuclei": True,
            "xss": True,
            "cors": True,
            "secret_js": True,
            "browser_session": True,
            "api_fuzzing": True,
            "sqli": True,
            "ssrf": True,
            "crlf": True,
            "takeover": True,
            "secret_repo": True,
            "scenario_runner": True,
            "ai_hypothesis": True,
            "idor_verification": True,
        }}
        supported_fields = set(getattr(FeatureFlags, "__dataclass_fields__", {{}}).keys())
        selected_flags = {{k: v for k, v in desired_flags.items() if k in supported_fields}}
        out["feature_flags_used"] = selected_flags

        ctx = ScanContext(
            scan_id="deep-trace-scan",
            program_id="deep-trace-program",
            scope=ScopeDefinition(in_scope=[{{"asset_type": "url", "value": TARGET}}], out_of_scope=[]),
            feature_flags=FeatureFlags(**selected_flags),
        )
        scope_filter = ScopeFilter(ctx.scope)
        assets = [DiscoveredAsset(asset_type="subdomain", value=TARGET)]

        # Nuclei preflight diagnostics
        t = time.time()
        try:
            version_proc = subprocess.run(
                ["nuclei", "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            templates_proc = subprocess.run(
                ["nuclei", "-tl"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            templates_stdout_lines = (templates_proc.stdout or "").splitlines()

            target_reachability = {{"ok": False, "status_code": None, "error": None}}
            try:
                resp = urllib.request.urlopen(TARGET, timeout=10)
                target_reachability["ok"] = True
                target_reachability["status_code"] = getattr(resp, "status", None)
            except Exception as exc:
                target_reachability["error"] = type(exc).__name__ + ": " + str(exc)

            preflight_status = (
                "completed"
                if version_proc.returncode == 0 and templates_proc.returncode == 0
                else "failed"
            )
            record(
                "stage4_nuclei_preflight",
                preflight_status,
                t,
                nuclei_version_rc=version_proc.returncode,
                nuclei_version_stdout=(version_proc.stdout or "").strip(),
                nuclei_version_stderr=(version_proc.stderr or "").strip(),
                nuclei_templates_rc=templates_proc.returncode,
                nuclei_templates_stdout_sample=templates_stdout_lines[:5],
                nuclei_templates_stdout_line_count=len(templates_stdout_lines),
                nuclei_templates_stderr=(templates_proc.stderr or "").strip(),
                target_reachability=target_reachability,
            )
        except Exception as exc:
            record("stage4_nuclei_preflight", "failed", t, error=str(exc))

        # Stage 2
        t = time.time()
        try:
            assets = await fingerprinting.run(ctx, assets, cfg)
            record(
                "stage2_fingerprinting",
                "completed",
                t,
                asset_count=len(assets),
                sample_assets=[a.value for a in assets[:5]],
            )
        except Exception as exc:
            record("stage2_fingerprinting", "failed", t, error=str(exc))
            out["summary"] = {{
                "asset_count": len(assets),
                "endpoint_count": 0,
                "js_asset_count": 0,
                "nuclei_finding_count": 0,
                "web_finding_count": 0,
                "js_secret_finding_count": 0,
            }}
            return

        # Stage 3
        t = time.time()
        endpoints = []
        js_assets = []
        try:
            endpoints, js_assets = await enumeration.run(ctx, assets, scope_filter, cfg)
            record(
                "stage3_enumeration",
                "completed",
                t,
                endpoint_count=len(endpoints),
                js_asset_count=len(js_assets),
                sample_endpoints=[
                    {{"url": e.full_url, "path": e.path, "status": e.response_code}}
                    for e in endpoints[:10]
                ],
            )
        except Exception as exc:
            record("stage3_enumeration", "failed", t, error=str(exc))

        # Stage 4
        t = time.time()
        nuclei_findings = []
        try:
            nuclei_findings = await nuclei_scan.run(ctx, assets, scope_filter, cfg)
            record(
                "stage4_nuclei",
                "completed",
                t,
                finding_count=len(nuclei_findings),
                sample_findings=[
                    {{
                        "type": f.vulnerability_type,
                        "title": f.title,
                        "severity": f.severity,
                        "url": f.affected_url,
                    }}
                    for f in nuclei_findings[:10]
                ],
            )
        except Exception as exc:
            record("stage4_nuclei", "failed", t, error=str(exc))

        # Stage 5
        t = time.time()
        web_findings = []
        try:
            web_findings = await web_vuln_tests.run(ctx, endpoints[:30], scope_filter, ctx.feature_flags)
            record(
                "stage5_web_vuln_tests",
                "completed",
                t,
                finding_count=len(web_findings),
                sample_findings=[
                    {{
                        "type": f.vulnerability_type,
                        "title": f.title,
                        "severity": f.severity,
                        "url": f.affected_url,
                    }}
                    for f in web_findings[:10]
                ],
            )
        except Exception as exc:
            record("stage5_web_vuln_tests", "failed", t, error=str(exc))

        # Stage 6
        t = time.time()
        js_secret_findings = []
        try:
            js_secret_findings = await js_secrets.run(ctx, js_assets)
            record(
                "stage6_js_secrets",
                "completed",
                t,
                finding_count=len(js_secret_findings),
                sample_findings=[
                    {{
                        "type": f.vulnerability_type,
                        "title": f.title,
                        "severity": f.severity,
                        "url": f.affected_url,
                    }}
                    for f in js_secret_findings[:10]
                ],
            )
        except Exception as exc:
            record("stage6_js_secrets", "failed", t, error=str(exc))

        out["summary"] = {{
            "asset_count": len(assets),
            "endpoint_count": len(endpoints),
            "js_asset_count": len(js_assets),
            "nuclei_finding_count": len(nuclei_findings),
            "web_finding_count": len(web_findings),
            "js_secret_finding_count": len(js_secret_findings),
        }}
    except Exception as exc:
        out["fatal_error"] = f"{{type(exc).__name__}}: {{exc}}"
        out["traceback"] = traceback.format_exc(limit=8)
    finally:
        out["summary"]["total_duration_seconds"] = round(time.time() - out["started_at"], 3)
        print("E2E_DIAG_JSON_START:" + json.dumps(out))

asyncio.run(main())
""".strip()


def _run_forced_deep_trace(obs: dict[str, Any], target_url: str) -> dict[str, Any]:
    script = _build_deep_trace_script(target_url)
    cmd = _compose_cmd("exec", "-T", "core-worker", "python", "-")
    result = _run_command(cmd, timeout=1800, input_text=script)
    _record_command(obs, "core-worker forced deep trace replay", cmd, result)
    diag = _parse_diag_json(result.stdout)
    return {
        "attempted": True,
        "target_url": target_url,
        "command_returncode": result.returncode,
        "diag": diag,
        "stdout_tail": _trim(result.stdout[-8000:]),
        "stderr_tail": _trim(result.stderr[-8000:]),
        "parse_error": None if diag is not None else "Could not parse deep trace JSON marker",
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None_"

    def _cell(value: Any) -> str:
        text = str(value) if value is not None else ""
        text = text.replace("|", "\\|").replace("\n", "<br>")
        return text

    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return "\n".join([header_line, sep_line, *row_lines])


def _write_report(obs: dict[str, Any]) -> None:
    lines: list[str] = []

    lines.append("# AttackBot End-to-End Findings Report")
    lines.append("")
    lines.append(f"- Generated at: `{_utc_now()}`")
    lines.append(f"- Report file: `{REPORT_PATH.name}`")
    lines.append(f"- Project root: `{ROOT_DIR}`")
    lines.append(f"- Test outcome: `{obs.get('outcome')}`")
    if obs.get("skip_reason"):
        lines.append(f"- Skip reason: `{obs.get('skip_reason')}`")
    if obs.get("error"):
        lines.append(f"- Error: `{obs.get('error')}`")
    lines.append("")

    lines.append("## Requested Mode")
    lines.append("- Full end-to-end execution attempted against current M3 stack.")
    lines.append("- All feature flags were set to `true` in scan start payload.")
    lines.append("- Live-mode policy: no seeded/dummy fallback for primary scan.")
    if PINNED_PROGRAM_HANDLE or PINNED_PROGRAM_ID:
        lines.append(
            "- Program selection override active via "
            "`E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`."
        )
    lines.append("")

    lines.append("## Execution Steps")
    if obs["steps"]:
        for step in obs["steps"]:
            lines.append(f"1. {step}")
    else:
        lines.append("_No steps captured._")
    lines.append("")

    lines.append("## Runtime Context")
    lines.append(f"- DB connection backend: `{obs.get('db_connection')}`")
    lines.append(f"- Live HackerOne mode: `{obs.get('live_hackerone_mode')}`")
    lines.append(f"- Program source: `{obs.get('program_source')}`")
    lines.append(
        f"- Program selection policy: `{obs.get('program_selection_policy')}`"
    )
    lines.append(
        f"- Pinned program handle override: `{obs.get('pinned_program_handle')}`"
    )
    lines.append(
        f"- Pinned program ID override: `{obs.get('pinned_program_id')}`"
    )
    lines.append(f"- Program ID: `{obs.get('program_id')}`")
    lines.append(f"- Program handle: `{obs.get('program_handle')}`")
    lines.append(f"- Scan ID: `{obs.get('scan_id')}`")
    lines.append(
        "- Reconciler pause requested (`E2E_PAUSE_RECONCILER`): "
        f"`{E2E_PAUSE_RECONCILER}`"
    )
    lines.append(
        "- Queue baseline enforcement (`E2E_ENFORCE_QUEUE_BASELINE`): "
        f"`{E2E_ENFORCE_QUEUE_BASELINE}`"
    )
    lines.append(
        "- Queue pre-purge enabled (`E2E_QUEUE_PURGE_BEFORE_BASELINE`): "
        f"`{E2E_QUEUE_PURGE_BEFORE_BASELINE}`"
    )
    credential_state = obs.get("credential_state") or {}
    lines.append(
        "- HackerOne username present in process env: "
        f"`{credential_state.get('username_present')}`"
    )
    lines.append(
        "- HackerOne token present in process env: "
        f"`{credential_state.get('token_present')}`"
    )
    deep_target = obs.get("forced_deep_trace_target") or {}
    if deep_target:
        lines.append(f"- Deep trace target URL: `{deep_target.get('target_url')}`")
        lines.append(f"- Deep trace target ready: `{deep_target.get('ready')}`")
    lines.append("")
    lines.append("### Enabled Feature Flags")
    lines.append("```json")
    lines.append(json.dumps(obs.get("feature_flags", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("## HackerOne Scrape Trigger")
    lines.append("```json")
    lines.append(json.dumps(obs.get("scrape_trigger_response", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("## Program Selection Audit")
    selection_rows = []
    for row in obs.get("program_selection_audit", []):
        selection_rows.append(
            [
                row.get("program_id"),
                row.get("handle"),
                row.get("name"),
                row.get("platform"),
                row.get("is_active"),
                row.get("valid_in_scope_count"),
                row.get("selected_for_this_run"),
                row.get("selection_reason"),
            ]
        )
    lines.append(
        _markdown_table(
            headers=[
                "program_id",
                "handle",
                "name",
                "platform",
                "is_active",
                "valid_in_scope_count",
                "selected",
                "reason",
            ],
            rows=selection_rows,
        )
    )
    lines.append("")

    lines.append("### Program Scope Used")
    scope_rows = []
    for row in obs.get("program_scope", []):
        scope_rows.append(
            [
                row.get("scope_type"),
                row.get("asset_type"),
                row.get("value"),
                row.get("notes"),
            ]
        )
    lines.append(
        _markdown_table(
            headers=["scope_type", "asset_type", "value", "notes"],
            rows=scope_rows,
        )
    )
    lines.append("")

    lines.append("## Service Health")
    health_rows = []
    for service, result in obs.get("service_health", {}).items():
        payload = result.get("body")
        status = ""
        if isinstance(payload, dict):
            status = payload.get("status", "")
        health_rows.append(
            [
                service,
                result.get("status_code"),
                status,
                result.get("error", ""),
            ]
        )
    lines.append(
        _markdown_table(
            headers=["service", "http_status", "health_status", "error"],
            rows=health_rows,
        )
    )
    lines.append("")

    lines.append("## Scan Summary")
    lines.append("### Start Response")
    lines.append("```json")
    lines.append(json.dumps(obs.get("scan_start_response", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("### Final Scan Row")
    lines.append("```json")
    lines.append(json.dumps(obs.get("scan_row", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("### Scan Wait Result")
    lines.append("```json")
    lines.append(json.dumps(obs.get("scan_wait", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("### Pipeline Stage Timeline")
    stage_rows = []
    for row in obs.get("scan_stages", []):
        stage_rows.append(
            [
                row.get("stage_number"),
                row.get("stage_name"),
                row.get("status"),
                row.get("started_at"),
                row.get("completed_at"),
                row.get("error_detail", ""),
            ]
        )
    lines.append(
        _markdown_table(
            headers=[
                "stage_number",
                "stage_name",
                "status",
                "started_at",
                "completed_at",
                "error_detail",
            ],
            rows=stage_rows,
        )
    )
    lines.append("")

    lines.append("### Artifact Counts")
    lines.append("```json")
    lines.append(json.dumps(obs.get("artifact_counts", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("### Findings by Severity")
    sev_rows = [
        [row.get("severity"), row.get("count")]
        for row in obs.get("severity_breakdown_rows", [])
    ]
    lines.append(_markdown_table(headers=["severity", "count"], rows=sev_rows))
    lines.append("")

    lines.append("### Findings by Source")
    src_rows = [
        [row.get("source"), row.get("count")]
        for row in obs.get("source_breakdown_rows", [])
    ]
    lines.append(_markdown_table(headers=["source", "count"], rows=src_rows))
    lines.append("")

    lines.append("### Detailed Findings")
    finding_rows = []
    for finding in obs.get("findings", []):
        finding_rows.append(
            [
                finding.get("finding_id"),
                finding.get("vulnerability_type"),
                finding.get("severity"),
                finding.get("cvss_score"),
                finding.get("affected_url"),
                finding.get("affected_parameter", ""),
                finding.get("source", ""),
                finding.get("is_verified"),
                finding.get("is_false_positive"),
            ]
        )
    lines.append(
        _markdown_table(
            headers=[
                "finding_id",
                "type",
                "severity",
                "cvss",
                "affected_url",
                "parameter",
                "source",
                "verified",
                "false_positive",
            ],
            rows=finding_rows,
        )
    )
    lines.append("")

    lines.append("## Queue and Worker Evidence")
    lines.append("### Core DLQ Inspect API")
    lines.append("```json")
    lines.append(json.dumps(obs.get("core_dlq_inspect", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("### Queue Baseline Purge")
    lines.append("```json")
    lines.append(json.dumps(obs.get("queue_baseline_purge", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("### Queue Baseline Wait")
    lines.append("```json")
    lines.append(json.dumps(obs.get("queue_baseline_wait", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("### RabbitMQ Queue States")
    queue_rows = []
    for row in obs.get("rabbitmq_queues", []):
        queue_rows.append(
            [
                row.get("queue"),
                row.get("exists"),
                row.get("messages"),
                row.get("messages_ready"),
                row.get("messages_unacknowledged"),
                row.get("consumers"),
                row.get("status_code", ""),
                row.get("error", ""),
            ]
        )
    lines.append(
        _markdown_table(
            headers=[
                "queue",
                "exists",
                "messages",
                "ready",
                "unacked",
                "consumers",
                "http_status",
                "error",
            ],
            rows=queue_rows,
        )
    )
    lines.append("")

    lines.append("## API Snapshots")
    lines.append("### /scans/{scan_id}")
    lines.append("```json")
    lines.append(json.dumps(obs.get("core_scan_api", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("### /scans/{scan_id}/findings")
    lines.append("```json")
    lines.append(json.dumps(obs.get("core_findings_api", {}), indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("## Forced Deep Trace (Downstream Replay)")
    deep = obs.get("forced_deep_trace") or {}
    if not deep:
        lines.append("_Not executed._")
        if obs.get("forced_deep_trace_disabled_reason"):
            lines.append(f"- Reason: `{obs.get('forced_deep_trace_disabled_reason')}`")
        lines.append("")
    else:
        lines.append(f"- Attempted: `{deep.get('attempted')}`")
        lines.append(f"- Target URL: `{deep.get('target_url')}`")
        lines.append(f"- Command return code: `{deep.get('command_returncode')}`")
        if deep.get("parse_error"):
            lines.append(f"- Parse error: `{deep.get('parse_error')}`")
        lines.append("")

        diag = deep.get("diag") or {}
        if diag:
            lines.append("### Deep Trace Summary")
            lines.append("```json")
            lines.append(json.dumps(diag.get("summary", {}), indent=2, sort_keys=True))
            lines.append("```")
            lines.append("")

            lines.append("### Deep Trace Stage Results")
            deep_rows = []
            for s in diag.get("stages", []):
                details = s.get("details", {})
                deep_rows.append(
                    [
                        s.get("name"),
                        s.get("status"),
                        s.get("duration_seconds"),
                        details.get("endpoint_count", details.get("asset_count", details.get("finding_count", ""))),
                        details.get("error", ""),
                    ]
                )
            lines.append(
                _markdown_table(
                    headers=["stage", "status", "duration_s", "count_hint", "error"],
                    rows=deep_rows,
                )
            )
            lines.append("")

            lines.append("### Deep Trace Raw JSON")
            lines.append("```json")
            lines.append(json.dumps(diag, indent=2, sort_keys=True))
            lines.append("```")
            lines.append("")
        else:
            lines.append("### Deep Trace Output (No Parsed JSON)")
            lines.append("```text")
            lines.append(deep.get("stdout_tail", ""))
            lines.append("```")
            lines.append("")

    lines.append("## Process Evidence")
    for command in obs.get("commands", []):
        lines.append(f"### Command: {command.get('label')}")
        lines.append(f"- Return code: `{command.get('returncode')}`")
        lines.append(f"- Command: `{command.get('cmd')}`")
        lines.append("")
        lines.append("```text")
        stdout = command.get("stdout") or ""
        stderr = command.get("stderr") or ""
        lines.append("STDOUT:")
        lines.append(stdout if stdout else "<empty>")
        lines.append("")
        lines.append("STDERR:")
        lines.append(stderr if stderr else "<empty>")
        lines.append("```")
        lines.append("")

    lines.append("## Observed Gaps in Current Implementation")
    lines.append("- Reporter worker currently validates `report.jobs` envelopes only.")
    lines.append("- Specialist workers are queue listeners; deeper stages land in later milestones.")
    lines.append("- This report reflects what ran in this test session, not aspirational docs.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.asyncio
async def test_end_to_end_system_trace_and_findings_documentation():
    obs: dict[str, Any] = {
        "steps": [],
        "commands": [],
        "outcome": "running",
        "skip_reason": None,
        "error": None,
        "service_health": {},
        "feature_flags": {},
        "db_connection": None,
        "live_hackerone_mode": LIVE_HACKERONE_ONLY,
        "pinned_program_handle": PINNED_PROGRAM_HANDLE,
        "pinned_program_id": PINNED_PROGRAM_ID,
        "program_selection_policy": None,
        "credential_state": {},
        "scrape_trigger_response": {},
        "program_selection_audit": [],
        "forced_deep_trace_disabled_reason": None,
        "program_source": None,
        "program_id": None,
        "program_handle": None,
        "program_scope": [],
        "scan_id": None,
        "queue_baseline_purge": {},
        "queue_baseline_wait": {},
        "scan_wait": {},
        "scan_start_response": {},
        "scan_row": {},
        "scan_stages": [],
        "findings": [],
        "artifact_counts": {},
        "severity_breakdown_rows": [],
        "source_breakdown_rows": [],
        "rabbitmq_queues": [],
        "core_scan_api": {},
        "core_findings_api": {},
        "core_dlq_inspect": {},
        "forced_deep_trace": {},
    }
    conn = None

    try:
        _log_step(obs, "Starting end-to-end system trace test")
        _ensure_env_file(obs)

        if not _docker_available():
            obs["outcome"] = "skipped"
            obs["skip_reason"] = "Docker daemon is not available"
            _log_step(obs, "Skipping: Docker daemon is not available")
            pytest.skip("Docker daemon is not available; cannot run end-to-end trace")

        _log_step(obs, "Bringing up stack with docker compose up -d")
        up_cmd = _compose_cmd("up", "-d")
        up_result = _run_command(up_cmd, timeout=900)
        _record_command(obs, "docker compose up -d", up_cmd, up_result)
        if up_result.returncode != 0:
            obs["outcome"] = "skipped"
            obs["skip_reason"] = "Failed to start docker compose stack"
            _log_step(obs, "Skipping: docker compose up -d returned non-zero")
            pytest.skip("Failed to start docker compose stack for end-to-end trace")

        ps_cmd = _compose_cmd("ps")
        ps_result = _run_command(ps_cmd, timeout=120)
        _record_command(obs, "docker compose ps", ps_cmd, ps_result)

        obs["service_health"] = await _collect_service_health(obs)
        scraper_ok = obs["service_health"]["scraper"].get("status_code") == 200
        core_ok = obs["service_health"]["core-engine"].get("status_code") == 200
        if not scraper_ok or not core_ok:
            raise AssertionError(
                "Core prerequisites not healthy (scraper and core-engine must both be 200)."
            )

        conn, db_connection = await _get_db_connection()
        obs["db_connection"] = db_connection
        _log_step(obs, f"Connected to database backend={db_connection}")

        username_present = bool(os.getenv("HACKERONE_API_USERNAME"))
        token_present = bool(os.getenv("HACKERONE_API_TOKEN"))
        obs["credential_state"] = {
            "username_present": username_present,
            "token_present": token_present,
        }
        if PINNED_PROGRAM_HANDLE or PINNED_PROGRAM_ID:
            _log_step(
                obs,
                "Pinned program selector configured: "
                f"E2E_PINNED_PROGRAM_ID={PINNED_PROGRAM_ID!r}, "
                f"E2E_PINNED_PROGRAM_HANDLE={PINNED_PROGRAM_HANDLE!r}",
            )

        if LIVE_HACKERONE_ONLY and (not username_present or not token_present):
            raise AssertionError(
                "Live HackerOne mode is enabled but credentials are missing in process env. "
                "Expected HACKERONE_API_USERNAME and HACKERONE_API_TOKEN."
            )

        if username_present and token_present:
            _log_step(obs, "HackerOne credentials detected; triggering live scraper sync")
            try:
                async with httpx.AsyncClient(timeout=240) as client:
                    trigger_resp = await client.post(
                        f"{SCRAPER_BASE_URL}/scrape/trigger",
                        params={"platform": "hackerone"},
                    )
                trigger_payload: Any
                try:
                    trigger_payload = trigger_resp.json()
                except Exception:
                    trigger_payload = trigger_resp.text
                obs["scrape_trigger_response"] = {
                    "status_code": trigger_resp.status_code,
                    "payload": _json_safe(trigger_payload),
                }
                _log_step(
                    obs,
                    f"Scraper trigger responded with status_code={trigger_resp.status_code}",
                )
            except Exception as exc:
                obs["scrape_trigger_response"] = {
                    "status_code": None,
                    "payload": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                _log_step(
                    obs,
                    "Scraper trigger request failed; continuing with current live program inventory. "
                    f"error={type(exc).__name__}: {exc}",
                )
        else:
            _log_step(obs, "HackerOne credentials not present in runtime env")

        if LIVE_HACKERONE_ONLY:
            selected_program, audit, selection_policy = await _select_live_hackerone_program(
                conn, obs
            )
            obs["program_selection_audit"] = audit
            obs["program_selection_policy"] = selection_policy
            if not selected_program:
                if selection_policy.startswith("pinned_"):
                    raise AssertionError(
                        "Pinned program selector did not resolve to any program after waiting "
                        f"{HACKERONE_PROGRAM_WAIT_SECONDS}s. "
                        f"E2E_PINNED_PROGRAM_ID={PINNED_PROGRAM_ID!r}, "
                        f"E2E_PINNED_PROGRAM_HANDLE={PINNED_PROGRAM_HANDLE!r}"
                    )
                raise AssertionError(
                    "No eligible HackerOne programs found after waiting "
                    f"{HACKERONE_PROGRAM_WAIT_SECONDS}s. "
                    "Eligible means platform=hackerone, active, at least one non-empty in_scope scope, "
                    "and not matching synthetic test handle prefixes."
                )
            if not _is_hackerone_eligible(selected_program):
                raise AssertionError(
                    "Pinned live program is not eligible for live HackerOne scan. "
                    "Expected platform=hackerone, active, at least one non-empty in_scope scope, "
                    "and non-synthetic handle. "
                    f"program_id={selected_program.get('program_id')} "
                    f"handle={selected_program.get('handle')}"
                )
            program_id = str(selected_program["program_id"])
            handle = str(selected_program.get("handle") or "")
            obs["program_source"] = (
                "hackerone_live_pinned"
                if selection_policy.startswith("pinned_")
                else "hackerone_live"
            )
            _log_step(
                obs,
                "Selected live HackerOne program for scan: "
                f"{program_id} ({handle}) via policy={selection_policy}",
            )
        else:
            inventory = await _list_program_inventory(conn, PROGRAM_AUDIT_LIMIT)
            selected, selection_policy = _find_program_by_pinned_selector(inventory)
            eligible = [
                p
                for p in inventory
                if int(p.get("valid_in_scope_count") or 0) > 0
                and p.get("is_active") is not False
                and not _is_synthetic_program(p)
            ]
            if selection_policy is None:
                selected = eligible[0] if eligible else None
                selection_policy = "most_recent_eligible_existing_real"
            selected_id = str(selected["program_id"]) if selected else None
            obs["program_selection_audit"] = _build_program_selection_audit(
                inventory,
                selected_id,
                selection_policy=selection_policy,
            )
            obs["program_selection_policy"] = selection_policy
            if not selected:
                if selection_policy.startswith("pinned_"):
                    raise AssertionError(
                        "Pinned program selector did not resolve to any program. "
                        f"E2E_PINNED_PROGRAM_ID={PINNED_PROGRAM_ID!r}, "
                        f"E2E_PINNED_PROGRAM_HANDLE={PINNED_PROGRAM_HANDLE!r}"
                    )
                raise AssertionError("No eligible real programs found with non-empty in_scope scope")
            if (
                int(selected.get("valid_in_scope_count") or 0) <= 0
                or selected.get("is_active") is False
                or _is_synthetic_program(selected)
            ):
                raise AssertionError(
                    "Selected program is not scan-eligible. "
                    "Expected active status, non-empty in_scope entries, and non-synthetic handle. "
                    f"program_id={selected.get('program_id')} handle={selected.get('handle')}"
                )
            program_id = str(selected["program_id"])
            handle = str(selected.get("handle") or "")
            obs["program_source"] = (
                "existing_real_pinned"
                if selection_policy.startswith("pinned_")
                else "existing_real"
            )
            _log_step(
                obs,
                "Selected existing real program with scope: "
                f"{program_id} ({handle}) via policy={selection_policy}",
            )

        obs["program_id"] = program_id
        obs["program_handle"] = handle
        obs["program_scope"] = await _fetch_program_scope(conn, program_id)

        queue_baseline_purge = await _purge_scan_jobs_for_baseline(obs)
        obs["queue_baseline_purge"] = queue_baseline_purge
        if E2E_ENFORCE_QUEUE_BASELINE and queue_baseline_purge.get("enabled") and not queue_baseline_purge.get("ok", True):
            raise AssertionError(
                "Queue purge failed before baseline enforcement. "
                f"details={queue_baseline_purge}"
            )

        feature_flags = _all_feature_flags_enabled()
        obs["feature_flags"] = feature_flags

        baseline_timeout_seconds = E2E_QUEUE_BASELINE_WAIT_SECONDS
        if queue_baseline_purge.get("enabled"):
            baseline_timeout_seconds = max(
                1,
                min(
                    E2E_QUEUE_BASELINE_WAIT_SECONDS,
                    E2E_QUEUE_POST_PURGE_BASELINE_WAIT_SECONDS,
                ),
            )

        _log_step(
            obs,
            "Waiting for queue baseline before triggering scan: "
            f"queue=scan.jobs ready=0 timeout={baseline_timeout_seconds}s",
        )
        queue_baseline_wait = await _wait_for_scan_jobs_queue_baseline(
            obs=obs,
            timeout_seconds=baseline_timeout_seconds,
            poll_seconds=E2E_QUEUE_BASELINE_POLL_SECONDS,
        )
        obs["queue_baseline_wait"] = queue_baseline_wait
        if queue_baseline_wait.get("reached"):
            _log_step(
                obs,
                "Queue baseline reached: "
                f"scan.jobs ready={queue_baseline_wait.get('state', {}).get('messages_ready')}",
            )
        elif E2E_ENFORCE_QUEUE_BASELINE:
            raise AssertionError(
                "Queue baseline not reached for scan.jobs before scan trigger. "
                f"waited={queue_baseline_wait.get('seconds_waited')}s "
                f"state={queue_baseline_wait.get('state')}"
            )
        else:
            _log_step(
                obs,
                "Queue baseline not reached but continuing because "
                "E2E_ENFORCE_QUEUE_BASELINE=false",
            )

        scan_request_started_at = datetime.now(timezone.utc)
        _log_step(obs, "Triggering core scan with all feature flags enabled")
        start_resp = await _start_scan(program_id=program_id, feature_flags=feature_flags)
        start_payload: Any
        try:
            start_payload = start_resp.json()
        except Exception:
            start_payload = start_resp.text
        obs["scan_start_response"] = {
            "status_code": start_resp.status_code,
            "payload": _json_safe(start_payload),
        }
        if start_resp.status_code != 200:
            raise AssertionError(
                f"Scan start failed with status={start_resp.status_code}: {start_payload}"
            )

        terminal_reached = False
        try:
            terminal_scan = await _wait_for_terminal_scan(
                conn=conn,
                program_id=program_id,
                created_after=scan_request_started_at,
                timeout_seconds=SCAN_TIMEOUT_SECONDS,
                obs=obs,
            )
            terminal_reached = True
            obs["scan_row"] = terminal_scan
            obs["scan_id"] = terminal_scan.get("scan_id")
            _log_step(obs, f"Terminal scan status reached: {terminal_scan.get('status')}")
            obs["scan_wait"] = {
                "terminal_reached": True,
                "timeout_seconds": SCAN_TIMEOUT_SECONDS,
                "status_at_snapshot": terminal_scan.get("status"),
            }
        except AssertionError as exc:
            if "Timed out waiting for terminal scan status" not in str(exc):
                raise
            _log_step(
                obs,
                f"Scan wait timed out after {SCAN_TIMEOUT_SECONDS}s; collecting live snapshot",
            )
            latest_scan = await _fetch_latest_scan_for_program(
                conn=conn,
                program_id=program_id,
                created_after=scan_request_started_at,
            )
            if latest_scan:
                obs["scan_row"] = latest_scan
                obs["scan_id"] = latest_scan.get("scan_id")
                _log_step(
                    obs,
                    f"Scan snapshot at timeout: status={latest_scan.get('status')}",
                )
                obs["scan_wait"] = {
                    "terminal_reached": False,
                    "timeout_seconds": SCAN_TIMEOUT_SECONDS,
                    "status_at_snapshot": latest_scan.get("status"),
                    "note": "Scan remained in progress beyond timeout window",
                }
            else:
                obs["scan_wait"] = {
                    "terminal_reached": False,
                    "timeout_seconds": SCAN_TIMEOUT_SECONDS,
                    "status_at_snapshot": None,
                    "note": "No scan row observed after start request",
                }

        if obs.get("scan_id"):
            detailed = await _collect_scan_data(conn, obs["scan_id"])
            obs.update(detailed)

            obs["core_scan_api"] = await _safe_get_json(
                f"{CORE_BASE_URL}/scans/{obs['scan_id']}"
            )
            obs["core_findings_api"] = await _safe_get_json(
                f"{CORE_BASE_URL}/scans/{obs['scan_id']}/findings"
            )
        else:
            _log_step(obs, "No scan_id available; skipped scan detail API/DB snapshots")

        obs["core_dlq_inspect"] = await _safe_get_json(
            f"{CORE_BASE_URL}/queue/dlq/inspect"
        )
        obs["rabbitmq_queues"] = await _collect_rabbitmq_queue_states()

        # Optional synthetic replay path (disabled by default for live-only runs).
        if (
            terminal_reached
            and len(obs.get("scan_stages", [])) <= 1
            and ENABLE_FORCED_DEEP_TRACE
        ):
            _log_step(
                obs,
                "Primary scan was shallow (<=1 stage). Starting forced deep downstream replay.",
            )
            deep_target = await _ensure_deep_trace_target(obs)
            obs["forced_deep_trace_target"] = deep_target
            if deep_target.get("ready"):
                obs["forced_deep_trace"] = _run_forced_deep_trace(
                    obs,
                    target_url=deep_target.get("target_url", DEEP_TRACE_TARGET_URL),
                )
                _log_step(obs, "Forced deep replay completed")
            else:
                obs["forced_deep_trace"] = {
                    "attempted": True,
                    "target_url": deep_target.get("target_url", DEEP_TRACE_TARGET_URL),
                    "command_returncode": None,
                    "diag": None,
                    "parse_error": "Deep trace target was not reachable in time",
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
                _log_step(obs, "Forced deep replay skipped: target not ready")
        elif len(obs.get("scan_stages", [])) <= 1:
            reason = (
                "Forced deep replay disabled in live mode "
                "(set E2E_ENABLE_FORCED_DEEP_TRACE=true to enable synthetic replay)"
            )
            obs["forced_deep_trace_disabled_reason"] = reason
            _log_step(obs, reason)

        since_arg = scan_request_started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        logs_cmd = _compose_cmd(
            "logs",
            "--no-color",
            "--since",
            since_arg,
            "--tail",
            str(PROCESS_LOG_TAIL),
            "scraper",
            "core-engine",
            "core-worker",
            "reporter",
            "reporter-worker",
        )
        logs_result = _run_command(logs_cmd, timeout=240)
        _record_command(
            obs,
            f"docker compose logs (tail {PROCESS_LOG_TAIL})",
            logs_cmd,
            logs_result,
        )

        reporter_worker_logs_cmd = _compose_cmd(
            "logs",
            "--no-color",
            "--since",
            since_arg,
            "--tail",
            str(REPORTER_WORKER_LOG_TAIL),
            "reporter-worker",
        )
        reporter_worker_logs_result = _run_command(reporter_worker_logs_cmd, timeout=240)
        _record_command(
            obs,
            f"docker compose logs reporter-worker (tail {REPORTER_WORKER_LOG_TAIL})",
            reporter_worker_logs_cmd,
            reporter_worker_logs_result,
        )

        if terminal_reached:
            assert obs["scan_row"]["status"] in {
                "completed",
                "partial",
                "failed_scope",
                "failed_internal",
            }
            obs["outcome"] = "completed"
        else:
            obs["outcome"] = "in_progress_timeout"
    except Exception as exc:
        obs["outcome"] = "failed"
        obs["error"] = str(exc)
        _log_step(obs, f"Failure captured: {exc}")
        raise
    finally:
        if conn is not None:
            await conn.close()
        _write_report(obs)
        assert REPORT_PATH.exists()
