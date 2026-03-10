"""
AttackBot scraper FastAPI routes.

Endpoints:
  POST /api/v1/scrape/trigger                  — manually trigger a scrape
  GET  /api/v1/programs                        — paginated program list
  GET  /api/v1/programs/{program_id}           — single program
  GET  /api/v1/programs/{program_id}/scope     — scope entries for a program
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from shared.logging import get_logger
from .repository import ProgramRepository

log    = get_logger(__name__)
router = APIRouter(prefix="/api/v1")
_repo  = ProgramRepository()

# ── Response models ────────────────────────────────────────────────────

class ScopeEntryResponse(BaseModel):
    scope_id:   uuid.UUID
    scope_type: str
    asset_type: str
    value:      str
    notes:      Optional[str] = None

    model_config = {"from_attributes": True}


class ProgramResponse(BaseModel):
    program_id:      uuid.UUID
    platform:        str
    handle:          str
    name:            Optional[str]     = None
    url:             Optional[str]     = None
    bounty_type:     Optional[str]     = None
    max_bounty:      Optional[int]     = None
    is_active:       bool
    queued_for_scan: bool
    last_scraped_at: Optional[datetime] = None
    created_at:      datetime

    model_config = {"from_attributes": True}


class ProgramListResponse(BaseModel):
    programs:  list[ProgramResponse]
    total:     int
    page:      int
    page_size: int


class TriggerResponse(BaseModel):
    status:  str
    message: str


# ── Routes ─────────────────────────────────────────────────────────────

@router.post("/scrape/trigger", response_model=TriggerResponse)
async def trigger_scrape(
    platform: str = Query(default="hackerone"),
) -> TriggerResponse:
    """
    Manually trigger an immediate scrape for the specified platform.
    Modifies the next_run_time on the APScheduler job to fire immediately.
    Returns immediately — the scrape runs in the background.
    """
    from .main import get_scheduler

    valid_platforms = ["hackerone"]
    if platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform {platform!r}. Valid platforms: {valid_platforms}",
        )

    scheduler = get_scheduler()
    job_id    = f"scrape_{platform}"
    job       = scheduler.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=500,
            detail=f"Scheduler job {job_id!r} not found. Is the scheduler running?",
        )

    job.modify(next_run_time=datetime.now())
    log.info("scrape_manually_triggered", platform=platform)

    return TriggerResponse(
        status  = "accepted",
        message = f"Scrape job for {platform!r} queued for immediate execution.",
    )


@router.get("/programs", response_model=ProgramListResponse)
async def list_programs(
    platform:  Optional[str]  = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    page:      int            = Query(default=1, ge=1),
    page_size: int            = Query(default=50, ge=1, le=200),
) -> ProgramListResponse:
    """Return a paginated list of programs with optional filters."""
    programs, total = await _repo.list_programs(
        platform  = platform,
        is_active = is_active,
        page      = page,
        page_size = page_size,
    )
    return ProgramListResponse(
        programs  = [ProgramResponse.model_validate(p, from_attributes=True) for p in programs],
        total     = total,
        page      = page,
        page_size = page_size,
    )


@router.get("/programs/{program_id}", response_model=ProgramResponse)
async def get_program(program_id: uuid.UUID) -> ProgramResponse:
    """Return a single program by ID."""
    program = await _repo.get_program_with_scopes(program_id)
    if not program:
        raise HTTPException(status_code=404, detail=f"Program {program_id} not found")
    return ProgramResponse.model_validate(program, from_attributes=True)


@router.get("/programs/{program_id}/scope", response_model=list[ScopeEntryResponse])
async def get_program_scope(program_id: uuid.UUID) -> list[ScopeEntryResponse]:
    """
    Return parsed scope entries for a program.
    Called by core-engine at scan start to build the Stage 0 ScopeFilter.
    """
    program = await _repo.get_program_with_scopes(program_id)
    if not program:
        raise HTTPException(status_code=404, detail=f"Program {program_id} not found")
    return [
        ScopeEntryResponse.model_validate(s, from_attributes=True)
        for s in program.scopes
    ]
