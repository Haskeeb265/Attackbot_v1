from unittest.mock import AsyncMock

import pytest

from backend.services.reporter import watchdog


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_recover_stale_reports_marks_rows_failed(monkeypatch):
    stale_rows = [
        {"report_id": "r1", "scan_id": "s1", "format": "pdf"},
        {"report_id": "r2", "scan_id": "s2", "format": "docx"},
    ]

    class _Repo:
        instances = []

        def __init__(self, session):
            self.mark_failed = AsyncMock()
            self.get_stale_generating_reports = AsyncMock(return_value=stale_rows)
            _Repo.instances.append(self)

    session = AsyncMock()
    monkeypatch.setattr(watchdog, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(watchdog, "ReportRepository", _Repo)

    recovered = await watchdog.recover_stale_reports(stale_minutes=30)

    assert recovered == 2
    # First repo instance handles stale query, remaining instances handle updates.
    assert _Repo.instances[0].get_stale_generating_reports.await_count == 1
    assert _Repo.instances[1].mark_failed.await_count == 1
    assert _Repo.instances[2].mark_failed.await_count == 1
