"""
Program repository — all DB operations for the scraper domain.

CRITICAL INVARIANT:
    queued_for_scan is EXCLUDED from the ON CONFLICT update clause in upsert().
    If a program exists with queued_for_scan=True (publish failed),
    a re-scrape must not clear that flag — the reconciler owns it.
    Violating this invariant causes silent loss of scan jobs.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text

from backend.services.scraper.models import Program
from backend.shared.db import get_session
from backend.shared.logging import get_logger

log = get_logger(__name__)


class ProgramRepository:

    async def upsert(self, program: Program) -> UUID:
        """
        Insert or update a program row.

        Returns the program_id (existing or newly created).
        queued_for_scan is intentionally excluded from the ON CONFLICT update set.
        """
        program_id = uuid4()
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            result = await session.execute(text("""
                INSERT INTO programs (
                    program_id, platform, handle, name, url,
                    bounty_type, max_bounty, is_active,
                    raw_policy, last_scraped_at, created_at, updated_at
                ) VALUES (
                    :program_id, :platform, :handle, :name, :url,
                    :bounty_type, :max_bounty, :is_active,
                    CAST(:raw_policy AS jsonb), :now, :now, :now
                )
                ON CONFLICT (handle) DO UPDATE SET
                    name              = EXCLUDED.name,
                    url               = EXCLUDED.url,
                    bounty_type       = EXCLUDED.bounty_type,
                    max_bounty        = EXCLUDED.max_bounty,
                    is_active         = EXCLUDED.is_active,
                    raw_policy        = EXCLUDED.raw_policy,
                    last_scraped_at   = EXCLUDED.last_scraped_at,
                    updated_at        = EXCLUDED.updated_at
                    -- queued_for_scan intentionally excluded --
                RETURNING program_id
            """), {
                "program_id": str(program_id),
                "platform": program.platform,
                "handle": program.handle,
                "name": program.name,
                "url": program.url,
                "bounty_type": program.bounty_type,
                "max_bounty": program.max_bounty,
                "is_active": program.is_active,
                "raw_policy": __import__("json").dumps(program.raw_policy or {}),
                "now": now,
            })
            row = result.fetchone()
            actual_id = UUID(str(row[0]))

        # Replace scope entries: delete existing, re-insert from this scrape.
        # This keeps scope in sync with the platform — old entries are never stale.
        await self._replace_scopes(actual_id, program)

        # Upsert policy (one row per program)
        if program.policy:
            await self._upsert_policy(actual_id, program)

        log.info("program_upserted", handle=program.handle, program_id=str(actual_id))
        return actual_id

    async def _replace_scopes(self, program_id: UUID, program: Program) -> None:
        """Delete and re-insert all scope entries for a program."""
        async with get_session() as session:
            await session.execute(
                text("DELETE FROM program_scopes WHERE program_id = :pid"),
                {"pid": str(program_id)},
            )
            for scope in program.scopes:
                await session.execute(text("""
                    INSERT INTO program_scopes
                        (scope_id, program_id, scope_type, asset_type, value, notes, created_at)
                    VALUES
                        (:scope_id, :program_id, :scope_type, :asset_type, :value, :notes, NOW())
                """), {
                    "scope_id": str(uuid4()),
                    "program_id": str(program_id),
                    "scope_type": scope.scope_type,
                    "asset_type": scope.asset_type,
                    "value": scope.value,
                    "notes": scope.notes,
                })

    async def _upsert_policy(self, program_id: UUID, program: Program) -> None:
        """Insert or update the policy row for a program."""
        async with get_session() as session:
            await session.execute(text("""
                INSERT INTO program_policies
                    (policy_id, program_id, disclosure_policy, testing_restrictions,
                     safe_harbor, created_at)
                VALUES
                    (:policy_id, :program_id, :disclosure_policy, :testing_restrictions,
                     :safe_harbor, NOW())
                ON CONFLICT (program_id) DO UPDATE SET
                    disclosure_policy    = EXCLUDED.disclosure_policy,
                    testing_restrictions = EXCLUDED.testing_restrictions,
                    safe_harbor          = EXCLUDED.safe_harbor
            """), {
                "policy_id": str(uuid4()),
                "program_id": str(program_id),
                "disclosure_policy": program.policy.disclosure_policy,
                "testing_restrictions": program.policy.testing_restrictions or [],
                "safe_harbor": program.policy.safe_harbor,
            })

    async def mark_queued(self, program_id: UUID) -> None:
        """Set queued_for_scan=True. Called by the publisher on publish failure."""
        async with get_session() as session:
            await session.execute(
                text("UPDATE programs SET queued_for_scan = true WHERE program_id = :pid"),
                {"pid": str(program_id)},
            )

    async def clear_queued(self, program_id: UUID) -> None:
        """Clear queued_for_scan=False. Called by the reconciler on publish success."""
        async with get_session() as session:
            await session.execute(
                text("UPDATE programs SET queued_for_scan = false WHERE program_id = :pid"),
                {"pid": str(program_id)},
            )

    async def get_queued_programs(self, max_age_days: int = 7) -> list[dict]:
        """
        Return all programs with queued_for_scan=True that were scraped recently.
        Programs older than max_age_days are not auto-retried (stale data risk).
        """
        async with get_session() as session:
            result = await session.execute(text(f"""
                SELECT program_id, platform, handle, name
                FROM programs
                WHERE queued_for_scan = true
                  AND last_scraped_at > NOW() - INTERVAL '{max_age_days} days'
                ORDER BY last_scraped_at DESC
            """))
            return [dict(row._mapping) for row in result.fetchall()]

    async def get_programs_due_for_scan(
        self,
        interval_minutes: int,
        batch_size: int,
    ) -> list[dict]:
        """
        Return active programs due for a background rescan.

        Eligibility rules:
          - has at least one non-empty in_scope entry
          - no in-flight scan row (queued/pending/running)
          - last terminal scan is older than interval_minutes (or never scanned)
        """
        async with get_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        p.program_id,
                        p.platform,
                        p.handle,
                        p.name
                    FROM programs p
                    WHERE p.is_active = true
                      AND EXISTS (
                        SELECT 1
                        FROM program_scopes ps
                        WHERE ps.program_id = p.program_id
                          AND ps.scope_type = 'in_scope'
                          AND BTRIM(COALESCE(ps.value, '')) <> ''
                      )
                      AND NOT EXISTS (
                        SELECT 1
                        FROM scans s_inflight
                        WHERE s_inflight.program_id = p.program_id
                          AND s_inflight.status IN ('queued', 'pending', 'running')
                      )
                      AND COALESCE(
                        (
                          SELECT MAX(COALESCE(s.completed_at, s.started_at, s.created_at))
                          FROM scans s
                          WHERE s.program_id = p.program_id
                            AND s.status IN (
                              'completed',
                              'partial',
                              'failed_scope',
                              'failed_internal',
                              'failed_auth'
                            )
                        ),
                        TO_TIMESTAMP(0)
                      ) <= NOW() - make_interval(mins => :interval_minutes)
                    ORDER BY
                      COALESCE(
                        (
                          SELECT MAX(COALESCE(s_any.completed_at, s_any.started_at, s_any.created_at))
                          FROM scans s_any
                          WHERE s_any.program_id = p.program_id
                        ),
                        TO_TIMESTAMP(0)
                      ) ASC,
                      p.updated_at DESC
                    LIMIT :batch_size
                    """
                ),
                {
                    "interval_minutes": interval_minutes,
                    "batch_size": batch_size,
                },
            )
            return [dict(row._mapping) for row in result.fetchall()]

    async def get_by_id(self, program_id: UUID) -> dict | None:
        async with get_session() as session:
            result = await session.execute(
                text("SELECT * FROM programs WHERE program_id = :pid"),
                {"pid": str(program_id)},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def get_scope(self, program_id: UUID) -> list[dict]:
        async with get_session() as session:
            result = await session.execute(
                text("SELECT * FROM program_scopes WHERE program_id = :pid ORDER BY scope_type"),
                {"pid": str(program_id)},
            )
            return [dict(row._mapping) for row in result.fetchall()]

    async def list_programs(
        self,
        page: int = 1,
        page_size: int = 50,
        platform: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        offset = (page - 1) * page_size
        conditions = []
        params: dict = {"limit": page_size, "offset": offset}

        if platform:
            conditions.append("platform = :platform")
            params["platform"] = platform
        if is_active is not None:
            conditions.append("is_active = :is_active")
            params["is_active"] = is_active

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        async with get_session() as session:
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM programs {where}"), params
            )
            total = count_result.scalar()

            result = await session.execute(
                text(
                    f"SELECT * FROM programs {where} "
                    f"ORDER BY created_at DESC "
                    f"LIMIT :limit OFFSET :offset"
                ),
                params,
            )
            items = [dict(row._mapping) for row in result.fetchall()]

        return {"total": total, "page": page, "page_size": page_size, "items": items}
