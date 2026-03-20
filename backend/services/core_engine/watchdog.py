from sqlalchemy import text

from backend.shared.db import get_session
from backend.shared.logging import get_logger

logger = get_logger("core_engine.watchdog")


async def recover_stuck_scans(republish_fn, stale_hours: int = 2) -> None:
    """
    APScheduler job. Finds scans stuck in 'running' for > stale_hours.
    Marks them failed_internal. Republishes if retry_count < 2.

    Without this, any Celery worker OOM-kill leaves status='running' forever.
    """
    async with get_session() as session:
        rows = await session.execute(
            text("""
                SELECT scan_id, retry_count, program_id
                FROM scans
                WHERE status = 'running'
                  AND started_at < NOW() - INTERVAL '""" + str(stale_hours) + """ hours'
            """)
        )
        stuck = rows.fetchall()

        for row in stuck:
            scan_id, retry_count, program_id = row
            logger.warning("Watchdog: marking stuck scan failed_internal",
                           scan_id=str(scan_id),
                           retry_count=retry_count)
            await session.execute(
                text("""
                    UPDATE scans
                    SET status = 'failed_internal',
                        error_detail = 'watchdog_timeout',
                        completed_at = NOW()
                    WHERE scan_id = :scan_id
                """),
                {"scan_id": str(scan_id)},
            )
            await session.commit()

            if retry_count < 2:
                try:
                    await republish_fn(program_id=str(program_id))
                    logger.info("Watchdog: republished scan for retry",
                                scan_id=str(scan_id))
                except Exception as e:
                    logger.error("Watchdog: republish failed",
                                 scan_id=str(scan_id), error=str(e))
            else:
                logger.warning("Watchdog: retry_count >= 2, not republishing",
                               scan_id=str(scan_id))
