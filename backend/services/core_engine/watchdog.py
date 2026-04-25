from datetime import datetime, timedelta, timezone
from typing import Optional

from prometheus_client import Counter, Gauge
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.repository import ScanRepository
from backend.shared.db import get_session
from backend.shared.logging import get_logger
from backend.shared.models.scans import Scan

logger = get_logger("core_engine.watchdog")

# Prometheus metrics
watchdog_executions = Counter(
    'watchdog_executions_total',
    'Total watchdog executions'
)
watchdog_scans_recovered = Counter(
    'watchdog_scans_recovered_total',
    'Total scans recovered by watchdog'
)
watchdog_errors = Counter(
    'watchdog_errors_total',
    'Total watchdog errors'
)
stuck_scans_gauge = Gauge(
    'stuck_scans_current',
    'Current number of stuck scans'
)


def _get_config() -> EngineConfig:
    """Lazy load config to avoid issues during import."""
    return EngineConfig()


async def recover_stuck_scans(republish_fn=None, stale_hours: int = 2):
    """
    APScheduler job. Finds scans stuck in 'running' for > stale_hours. 
    Marks them failed_internal. Republishes if retry_count < 2.
    
    Without this, any Celery worker OOM-kill leaves status='running' forever.
    
    This function:
    1. Queries for scans with status='running' that started before threshold
    2. Marks each as failed_internal with error detail
    3. Logs recovery actions and metrics
    4. Re-raises exceptions to ensure visibility
    
    Args:
        republish_fn: Optional function to republish scans for retry
        stale_hours: Threshold in hours (default: 2)
    """
    execution_start = datetime.now(timezone.utc)
    
    logger.info(
        "Watchdog starting scan recovery check",
        threshold_hours=stale_hours,
        execution_time=execution_start.isoformat()
    )
    
    watchdog_executions.inc()
    
    try:
        threshold_seconds = stale_hours * 3600
        
        async with get_session() as session:
            repo = ScanRepository(session)
            
            # Calculate threshold with explicit timezone
            threshold = datetime.now(timezone.utc) - timedelta(
                seconds=threshold_seconds
            )
            
            logger.info(
                "Watchdog threshold calculated",
                threshold=threshold.isoformat(),
                current_time=datetime.now(timezone.utc).isoformat()
            )
            
            # Query for stuck scans with explicit status filter
            result = await session.execute(
                select(Scan)
                .where(Scan.status == "running")
                .where(Scan.started_at < threshold)
            )
            stuck_scans = result.scalars().all()
            
            scan_count = len(stuck_scans)
            stuck_scans_gauge.set(scan_count)
            
            logger.info(
                "Watchdog found stuck scans",
                count=scan_count,
                scan_ids=[str(s.scan_id) for s in stuck_scans]
            )
            
            if scan_count == 0:
                logger.info("Watchdog completed: no stuck scans found")
                return
            
            # Process each stuck scan
            recovered_count = 0
            for scan in stuck_scans:
                runtime = datetime.now(timezone.utc) - scan.started_at
                
                logger.warning(
                    "Recovering stuck scan",
                    scan_id=str(scan.scan_id),
                    program_id=str(scan.program_id),
                    started_at=scan.started_at.isoformat() if scan.started_at else None,
                    runtime_seconds=runtime.total_seconds(),
                    threshold_seconds=threshold_seconds
                )
                
                try:
                    error_detail = f"Watchdog recovery: scan exceeded {threshold_seconds}s threshold (runtime: {runtime.total_seconds()}s)"
                    
                    # Mark scan as failed_internal
                    await repo.mark_scan_complete(
                        scan_id=scan.scan_id,
                        status="failed_internal",
                        finding_count=0,
                        severity_breakdown={},
                        error_detail=error_detail
                    )
                    
                    recovered_count += 1
                    watchdog_scans_recovered.inc()
                    
                    logger.info(
                        "Successfully recovered stuck scan",
                        scan_id=str(scan.scan_id),
                        runtime_seconds=runtime.total_seconds()
                    )
                    
                    # Republish if retry_count < 2 and republish_fn provided
                    if republish_fn and scan.retry_count < 2:
                        try:
                            await republish_fn(program_id=str(scan.program_id))
                            logger.info("Watchdog: republished scan for retry",
                                       scan_id=str(scan.scan_id))
                        except Exception as e:
                            logger.error("Watchdog: republish failed",
                                        scan_id=str(scan.scan_id), error=str(e))
                    elif republish_fn:
                        logger.warning("Watchdog: retry_count >= 2, not republishing",
                                      scan_id=str(scan.scan_id))
                                
                except Exception as scan_error:
                    logger.error(
                        "Failed to recover individual scan",
                        scan_id=str(scan.scan_id),
                        error=str(scan_error),
                        exc_info=True
                    )
                    # Continue processing other scans
            
            execution_duration = (datetime.now(timezone.utc) - execution_start).total_seconds()
            
            logger.info(
                "Watchdog completed",
                scans_found=scan_count,
                scans_recovered=recovered_count,
                execution_duration_seconds=execution_duration
            )
            
    except Exception as e:
        watchdog_errors.inc()
        logger.error(
            "Watchdog recovery failed critically",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        # Re-raise to ensure visibility in logs and metrics
        raise


def start_watchdog(scheduler: AsyncIOScheduler):
    """
    Register watchdog job with scheduler.
    
    Args:
        scheduler: APScheduler instance
    """
    config = _get_config()
    
    logger.info(
        "Registering watchdog job",
        interval_seconds=config.watchdog_interval_seconds,
        stale_threshold_hours=config.watchdog_stale_threshold_hours
    )
    
    scheduler.add_job(
        recover_stuck_scans,
        trigger='interval',
        seconds=config.watchdog_interval_seconds,
        kwargs={"stale_hours": config.watchdog_stale_threshold_hours},
        id='scan_watchdog',
        replace_existing=True,
        max_instances=1,  # Prevent overlapping executions
        coalesce=True,    # Combine missed runs into one
        misfire_grace_time=30  # Allow 30s grace period for missed runs
    )
    
    logger.info("Watchdog job registered successfully")
