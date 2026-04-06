import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

try:
    from backend.services.core_engine import main as core_main
except ModuleNotFoundError as exc:
    if exc.name == "kombu":
        core_main = None
    else:
        raise


pytestmark = pytest.mark.skipif(core_main is None, reason="kombu not installed")


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_get_findings_returns_legacy_and_additive_fields(monkeypatch):
    finding_id = uuid4()
    created_at = datetime.now(timezone.utc)
    raw_output = {"info": {"description": "scanner desc"}}

    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=_Result(
            [
                (
                    finding_id,
                    "xss",
                    "Reflected XSS",
                    "high",
                    7.5,
                    "https://example.com/search",
                    "q",
                    False,
                    "nuclei",
                    created_at,
                    "Top-level description",
                    "Step 1, Step 2",
                    raw_output,
                )
            ]
        )
    )
    monkeypatch.setattr(core_main, "get_session", lambda: _SessionContext(session))

    response = await core_main.get_findings(scan_id=str(uuid4()))
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert body["count"] == 1
    finding = body["findings"][0]

    # Legacy contract remains intact.
    assert finding["finding_id"] == str(finding_id)
    assert finding["vulnerability_type"] == "xss"
    assert finding["title"] == "Reflected XSS"
    assert finding["severity"] == "high"
    assert finding["cvss_score"] == 7.5
    assert finding["affected_url"] == "https://example.com/search"
    assert finding["affected_parameter"] == "q"
    assert finding["is_verified"] is False
    assert finding["source"] == "nuclei"
    assert finding["created_at"] == created_at.isoformat()

    # Additive fields for reporter enrichment.
    assert finding["description"] == "Top-level description"
    assert finding["reproduction_steps"] == "Step 1, Step 2"
    assert finding["raw_output"] == raw_output
