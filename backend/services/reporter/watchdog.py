from __future__ import annotations

from backend.services.reporter.repository import ReportRepository
from backend.shared.db import get_session
from backend.shared.logging import get_logger

log = get_logger(__name__)


async def recover_stale_reports(stale_minutes: int) -> int:
    """
    Mark stale generating report rows as failed with watchdog_timeout.
    Returns the number of rows transitioned.
    """
    async with get_session() as session:
        repository = ReportRepository(session)
        stale_rows = await repository.get_stale_generating_reports(stale_minutes=stale_minutes)

    recovered = 0
    for row in stale_rows:
        async with get_session() as session:
            repository = ReportRepository(session)
            await repository.mark_failed(
                report_id=row["report_id"],
                error_detail="watchdog_timeout",
            )
        recovered += 1
        log.warning(
            "report_watchdog_marked_failed",
            report_id=row["report_id"],
            scan_id=row["scan_id"],
            format=row["format"],
            reason="watchdog_timeout",
        )

    return recovered
