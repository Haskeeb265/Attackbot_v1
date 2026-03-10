"""
AttackBot scraper repository.

Owns all database reads and writes for the scraper domain:
  - programs, program_scopes, program_policies

Critical invariant:
  queued_for_scan is NEVER reset by upsert().
  Only the reconciler and ScanJobPublisher touch that flag.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import select, update, func as sa_func, text as sa_text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shared.db import get_session
from shared.logging import get_logger
from .models import Program, ProgramScope, ProgramPolicy
from .collectors.models import RawProgram
from .scope_parser import ScopeParser, ParsedScope

log           = get_logger(__name__)
_scope_parser = ScopeParser()


class ProgramRepository:
    """Repository for all scraper domain DB operations."""

    # ── Upsert ────────────────────────────────────────────────────

    async def upsert(
        self,
        raw: RawProgram,
        normalized: dict,
    ) -> tuple[uuid.UUID, bool]:
        """
        Insert or update a program and its scopes.
        Returns (program_id, created: bool).

        Critical behaviour:
          - queued_for_scan is NEVER in the ON CONFLICT SET clause
          - Scopes are fully replaced on every upsert (delete + re-insert)
          - last_scraped_at is always updated
          - raw_policy is preserved as a verbatim snapshot
        """
        async with get_session() as session:
            now = datetime.now(timezone.utc)

            # ── Upsert programs row ────────────────────────────────
            insert_stmt = pg_insert(Program).values(
                platform        = normalized["platform"],
                handle          = normalized["handle"],
                name            = normalized["name"],
                url             = normalized["url"],
                bounty_type     = normalized["bounty_type"],
                max_bounty      = normalized["max_bounty"],
                is_active       = normalized["is_active"],
                raw_policy      = normalized["raw_policy"],
                last_scraped_at = now,
                queued_for_scan = False,   # only set on INSERT, not UPDATE
                created_at      = now,
                updated_at      = now,
            ).on_conflict_do_update(
                index_elements=["handle"],
                set_={
                    "name":            normalized["name"],
                    "url":             normalized["url"],
                    "bounty_type":     normalized["bounty_type"],
                    "max_bounty":      normalized["max_bounty"],
                    "is_active":       normalized["is_active"],
                    "raw_policy":      normalized["raw_policy"],
                    "last_scraped_at": now,
                    "updated_at":      now,
                    # INTENTIONALLY OMITTED: queued_for_scan
                    # Never reset a True flag via rescrape — reconciler owns it.
                },
            ).returning(
                Program.program_id,
                Program.created_at,
                Program.updated_at,
            )

            result     = await session.execute(insert_stmt)
            row        = result.fetchone()
            program_id = row.program_id
            # created = True when created_at ≈ updated_at (both just set)
            created    = abs((row.updated_at - row.created_at).total_seconds()) < 1

            # ── Replace scopes ─────────────────────────────────────
            # Full replace: delete all existing, re-insert fresh.
            # Simpler and safer than a three-way diff.
            await session.execute(
                sa.delete(ProgramScope).where(
                    ProgramScope.program_id == program_id
                )
            )

            parsed_scopes: list[ParsedScope] = _scope_parser.parse_all(raw.scopes)
            for ps in parsed_scopes:
                session.add(ProgramScope(
                    program_id = program_id,
                    scope_type = ps.scope_type,
                    asset_type = ps.asset_type,
                    value      = ps.value,
                    notes      = ps.notes or "",
                ))

            # ── Upsert policy ──────────────────────────────────────
            if raw.policy:
                policy_stmt = pg_insert(ProgramPolicy).values(
                    program_id            = program_id,
                    disclosure_policy     = raw.policy.disclosure_policy,
                    testing_restrictions  = raw.policy.testing_restrictions or [],
                    safe_harbor           = raw.policy.safe_harbor,
                    created_at            = now,
                ).on_conflict_do_update(
                    index_elements=["program_id"],
                    set_={
                        "disclosure_policy":    raw.policy.disclosure_policy,
                        "testing_restrictions": raw.policy.testing_restrictions or [],
                        "safe_harbor":          raw.policy.safe_harbor,
                    },
                )
                await session.execute(policy_stmt)

            log.info(
                "program_upserted",
                handle     = normalized["handle"],
                program_id = str(program_id),
                created    = created,
                scopes     = len(parsed_scopes),
            )
            return program_id, created

    # ── Flag management ────────────────────────────────────────────

    async def set_queued_for_scan(
        self,
        program_id: uuid.UUID,
        queued: bool,
    ) -> None:
        """Set the queued_for_scan flag. Called by publisher and reconciler."""
        async with get_session() as session:
            await session.execute(
                update(Program)
                .where(Program.program_id == program_id)
                .values(queued_for_scan=queued)
            )

    # ── Queries ────────────────────────────────────────────────────

    async def get_programs_pending_reconcile(
        self,
        stale_days: int = 7,
    ) -> list[Program]:
        """
        Return programs that failed to publish and are within the active window.
        Only programs scraped within the last stale_days days are eligible —
        older ones may have changed scope and should be re-scraped first.
        """
        async with get_session() as session:
            result = await session.execute(
                select(Program).where(
                    Program.queued_for_scan == True,
                    Program.last_scraped_at > sa_text(
                        f"NOW() - INTERVAL '{int(stale_days)} days'"
                    ),
                )
            )
            return list(result.scalars().all())

    async def get_program_with_scopes(
        self,
        program_id: uuid.UUID,
    ) -> Optional[Program]:
        """Fetch a program and eagerly load its scopes."""
        async with get_session() as session:
            result = await session.execute(
                select(Program).where(Program.program_id == program_id)
            )
            program = result.scalar_one_or_none()
            if program:
                # Trigger scope load within the session
                await session.refresh(program, attribute_names=["scopes"])
            return program

    async def get_program_by_handle(self, handle: str) -> Optional[Program]:
        """Fetch a program by its platform handle."""
        async with get_session() as session:
            result = await session.execute(
                select(Program).where(Program.handle == handle)
            )
            return result.scalar_one_or_none()

    async def list_programs(
        self,
        platform: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Program], int]:
        """Return a paginated list of programs with optional filters."""
        async with get_session() as session:
            query = select(Program)

            if platform is not None:
                query = query.where(Program.platform == platform)
            if is_active is not None:
                query = query.where(Program.is_active == is_active)

            # Count
            count_query = select(sa_func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total = count_result.scalar_one()

            # Page
            result = await session.execute(
                query
                .order_by(Program.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            return list(result.scalars().all()), total
