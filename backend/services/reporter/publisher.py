from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.shared.logging import get_logger
from backend.shared.queue import QueuePublisher, Queues
from backend.shared.schemas.reports_completed import (
    ReportsCompletedPayload,
    build_reports_completed_message,
)

log = get_logger(__name__)


class ReportsCompletedPublisher:
    def __init__(self, queue_publisher: QueuePublisher) -> None:
        self._publisher = queue_publisher

    async def publish_report_completed(self, report: dict[str, Any]) -> bool:
        payload = ReportsCompletedPayload(
            report_id=report["report_id"],
            scan_id=report["scan_id"],
            program_id=report["program_id"],
            format=report["format"],
            status=report["status"],
            storage_path=report["storage_path"],
            file_size_bytes=report["file_size_bytes"],
            generated_at=(
                datetime.fromisoformat(report["generated_at"])
                if report.get("generated_at")
                else datetime.now(timezone.utc)
            ),
        )
        message = build_reports_completed_message(payload)
        success = await self._publisher.publish(Queues.REPORTS_COMPLETED, message)
        if not success:
            log.error(
                "publish_reports_completed_failed",
                report_id=report["report_id"],
                note="artifact is still available - publish failure is non-fatal",
            )
        return success
