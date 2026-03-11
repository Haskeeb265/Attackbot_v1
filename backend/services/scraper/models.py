"""
Internal scraper data models.

These are pure Python dataclasses — no SQLAlchemy, no Pydantic.
They represent the canonical in-memory objects that flow between:

    collector → scope_parser → repository

They are NOT the database schema.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RawProgram:
    """
    Raw response from a platform API — platform-specific fields, not normalized.
    Passed directly from fetch_listing() / fetch_details() to normalize().
    """
    platform: str
    raw_data: dict           # full API response, unmodified
    handle: str              # unique identifier on the platform
    fetched_at: str          # ISO8601 timestamp of when this was fetched


@dataclass
class ProgramScope:
    """A single scope entry — result of parsing one raw scope line."""
    scope_type: str          # "in_scope" | "out_of_scope"
    asset_type: str          # "url" | "domain" | "wildcard_domain" | "ip_range" | "mobile_app" | "api"
    value: str               # the actual scope value (e.g. "*.example.com", "192.168.1.0/24")
    notes: Optional[str] = None


@dataclass
class ProgramPolicy:
    """Extracted policy details for a program."""
    disclosure_policy: Optional[str] = None
    testing_restrictions: list[str] = field(default_factory=list)
    safe_harbor: Optional[bool] = None


@dataclass
class Program:
    """
    Canonical normalized program — output of any collector's normalize() method.
    This is what gets upserted into the DB.
    Every collector must produce this exact shape.
    """
    platform: str
    handle: str
    name: str
    url: Optional[str] = None
    bounty_type: Optional[str] = None       # "bug_bounty" | "vdp"
    max_bounty: Optional[int] = None
    is_active: bool = True
    raw_policy: Optional[dict] = None       # stored as JSONB for reference
    scopes: list[ProgramScope] = field(default_factory=list)
    policy: Optional[ProgramPolicy] = None