from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ReportRepository:
    """Persistence operations for reporter domain tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_or_reset_report(self, scan_id: str, program_id: str, format_name: str) -> str:
        result = await self.session.execute(
            text(
                """
                INSERT INTO reports (
                    report_id, scan_id, program_id, format, status,
                    storage_path, file_size_bytes, error_detail, generated_at, created_at
                ) VALUES (
                    :report_id, :scan_id, :program_id, :format_name, 'generating',
                    NULL, NULL, NULL, NULL, NOW()
                )
                ON CONFLICT (scan_id, format) DO UPDATE SET
                    program_id = EXCLUDED.program_id,
                    status = 'generating',
                    storage_path = NULL,
                    file_size_bytes = NULL,
                    error_detail = NULL,
                    generated_at = NULL
                RETURNING report_id
                """
            ),
            {
                "report_id": str(uuid.uuid4()),
                "scan_id": scan_id,
                "program_id": program_id,
                "format_name": format_name,
            },
        )
        row = result.fetchone()
        await self.session.commit()
        return str(row[0])

    async def mark_generating(self, report_id: str) -> None:
        await self.session.execute(
            text(
                """
                UPDATE reports
                SET status = 'generating',
                    error_detail = NULL,
                    storage_path = NULL,
                    file_size_bytes = NULL,
                    generated_at = NULL
                WHERE report_id = :report_id
                """
            ),
            {"report_id": report_id},
        )
        await self.session.commit()

    async def mark_completed(self, report_id: str, storage_path: str, file_size_bytes: int) -> None:
        await self.session.execute(
            text(
                """
                UPDATE reports
                SET status = 'completed',
                    storage_path = :storage_path,
                    file_size_bytes = :file_size_bytes,
                    error_detail = NULL,
                    generated_at = NOW()
                WHERE report_id = :report_id
                """
            ),
            {
                "report_id": report_id,
                "storage_path": storage_path,
                "file_size_bytes": file_size_bytes,
            },
        )
        await self.session.commit()

    async def mark_partial(
        self,
        report_id: str,
        storage_path: str,
        file_size_bytes: int,
        reason: str,
    ) -> None:
        await self.session.execute(
            text(
                """
                UPDATE reports
                SET status = 'partial',
                    storage_path = :storage_path,
                    file_size_bytes = :file_size_bytes,
                    error_detail = :reason,
                    generated_at = NOW()
                WHERE report_id = :report_id
                """
            ),
            {
                "report_id": report_id,
                "storage_path": storage_path,
                "file_size_bytes": file_size_bytes,
                "reason": reason,
            },
        )
        await self.session.commit()

    async def mark_failed(self, report_id: str, error_detail: str) -> None:
        await self.session.execute(
            text(
                """
                UPDATE reports
                SET status = 'failed',
                    error_detail = :error_detail
                WHERE report_id = :report_id
                """
            ),
            {
                "report_id": report_id,
                "error_detail": error_detail,
            },
        )
        await self.session.commit()

    async def replace_reproduction_packs(self, report_id: str, packs: list[Any]) -> None:
        await self.session.execute(
            text("DELETE FROM reproduction_packs WHERE report_id = :report_id"),
            {"report_id": report_id},
        )
        for pack in packs:
            if isinstance(pack, dict):
                finding_id = str(pack["finding_id"])
                curl_command = pack.get("curl_command")
                http_request_raw = pack.get("http_request_raw")
                browser_steps = pack.get("browser_steps")
                notes = pack.get("notes")
            else:
                finding_id = str(pack.finding_id)
                curl_command = pack.curl_command
                http_request_raw = pack.http_request_raw
                browser_steps = pack.browser_steps
                notes = pack.notes
            await self.session.execute(
                text(
                    """
                    INSERT INTO reproduction_packs (
                        pack_id, finding_id, report_id, curl_command,
                        http_request_raw, browser_steps, notes, created_at
                    ) VALUES (
                        :pack_id, :finding_id, :report_id, :curl_command,
                        :http_request_raw, :browser_steps, :notes, NOW()
                    )
                    """
                ),
                {
                    "pack_id": str(uuid.uuid4()),
                    "finding_id": finding_id,
                    "report_id": report_id,
                    "curl_command": curl_command,
                    "http_request_raw": http_request_raw,
                    "browser_steps": browser_steps,
                    "notes": notes,
                },
            )
        await self.session.commit()

    async def list_reports(
        self,
        page: int,
        page_size: int,
        scan_id_filter: str | None,
        status_filter: str | None,
    ) -> dict[str, Any]:
        conditions: list[str] = []
        params: dict[str, Any] = {
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        if scan_id_filter:
            conditions.append("scan_id = :scan_id")
            params["scan_id"] = scan_id_filter
        if status_filter:
            conditions.append("status = :status")
            params["status"] = status_filter

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_result = await self.session.execute(
            text(f"SELECT COUNT(*) FROM reports {where}"),
            params,
        )
        total = int(count_result.scalar() or 0)

        rows = await self.session.execute(
            text(
                f"""
                SELECT report_id, scan_id, program_id, format, status, storage_path,
                       file_size_bytes, error_detail, generated_at, created_at
                FROM reports
                {where}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        items = [self._row_to_dict(row) for row in rows.fetchall()]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        rows = await self.session.execute(
            text(
                """
                SELECT report_id, scan_id, program_id, format, status, storage_path,
                       file_size_bytes, error_detail, generated_at, created_at
                FROM reports
                WHERE report_id = :report_id
                """
            ),
            {"report_id": report_id},
        )
        row = rows.fetchone()
        return self._row_to_dict(row) if row else None

    async def get_reports_by_scan(self, scan_id: str) -> list[dict[str, Any]]:
        rows = await self.session.execute(
            text(
                """
                SELECT report_id, scan_id, program_id, format, status, storage_path,
                       file_size_bytes, error_detail, generated_at, created_at
                FROM reports
                WHERE scan_id = :scan_id
                ORDER BY created_at DESC
                """
            ),
            {"scan_id": scan_id},
        )
        return [self._row_to_dict(row) for row in rows.fetchall()]

    async def get_stale_generating_reports(self, stale_minutes: int) -> list[dict[str, Any]]:
        rows = await self.session.execute(
            text(
                """
                SELECT report_id, scan_id, program_id, format, status, storage_path,
                       file_size_bytes, error_detail, generated_at, created_at
                FROM reports
                WHERE status = 'generating'
                  AND created_at < NOW() - (:stale_minutes * INTERVAL '1 minute')
                ORDER BY created_at ASC
                """
            ),
            {"stale_minutes": stale_minutes},
        )
        return [self._row_to_dict(row) for row in rows.fetchall()]

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        return {
            "report_id": str(row[0]),
            "scan_id": str(row[1]),
            "program_id": str(row[2]),
            "format": row[3],
            "status": row[4],
            "storage_path": row[5],
            "file_size_bytes": row[6],
            "error_detail": row[7],
            "generated_at": row[8].isoformat() if row[8] else None,
            "created_at": row[9].isoformat() if row[9] else None,
        }
