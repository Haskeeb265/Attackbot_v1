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

    def fetchone(self):
        return self._rows[0] if self._rows else None

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
async def test_get_finding_evidence_returns_items(monkeypatch):
    scan_id = str(uuid4())
    finding_id = str(uuid4())
    evidence_id = uuid4()
    captured_at = datetime.now(timezone.utc)

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _Result([(finding_id,)]),
            _Result(
                [
                    (
                        evidence_id,
                        "screenshot",
                        f"evidence/{finding_id}/shot.png",
                        "Browser screenshot",
                        captured_at,
                    )
                ]
            ),
        ]
    )
    monkeypatch.setattr(core_main, "get_session", lambda: _SessionContext(session))

    response = await core_main.get_finding_evidence(scan_id=scan_id, finding_id=finding_id)
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert body["scan_id"] == scan_id
    assert body["finding_id"] == finding_id
    assert len(body["items"]) == 1
    assert body["items"][0]["evidence_id"] == str(evidence_id)
    assert body["items"][0]["artifact_type"] == "screenshot"


@pytest.mark.asyncio
async def test_get_finding_evidence_returns_empty_items_when_none_exist(monkeypatch):
    scan_id = str(uuid4())
    finding_id = str(uuid4())

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _Result([(finding_id,)]),
            _Result([]),
        ]
    )
    monkeypatch.setattr(core_main, "get_session", lambda: _SessionContext(session))

    response = await core_main.get_finding_evidence(scan_id=scan_id, finding_id=finding_id)
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert body["scan_id"] == scan_id
    assert body["finding_id"] == finding_id
    assert body["items"] == []


@pytest.mark.asyncio
async def test_get_finding_evidence_returns_404_for_scan_finding_mismatch(monkeypatch):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[_Result([])])
    monkeypatch.setattr(core_main, "get_session", lambda: _SessionContext(session))

    response = await core_main.get_finding_evidence(scan_id=str(uuid4()), finding_id=str(uuid4()))
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 404
    assert body["error"] == "not found"
    assert session.execute.await_count == 1
