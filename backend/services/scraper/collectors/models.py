"""
Raw data models for platform collectors.
These are intermediate representations — not ORM models.
The collector fetches data into these, then normalize() maps them to DB dicts.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawScopeEntry:
    """Direct mapping from platform API — not yet validated or typed."""
    asset_type: str    # platform-specific string, mapped to canonical in ScopeParser
    value:      str
    scope_type: str    # 'in_scope' | 'out_of_scope'
    notes:      str = ""


@dataclass
class RawPolicy:
    """Program policy data as received from the platform."""
    disclosure_policy:    str       = ""
    testing_restrictions: list[str] = field(default_factory=list)
    safe_harbor:          bool | None = None


@dataclass
class RawProgram:
    """
    Unprocessed program data as fetched from the platform API.
    All fields are primitive Python types — no ORM or Pydantic models.
    Normalization happens in BaseCollector.normalize().
    """
    platform:    str
    handle:      str
    name:        str
    url:         str
    bounty_type: str
    max_bounty:  int | None
    is_active:   bool
    raw_policy:  dict[str, Any]
    scopes:      list[RawScopeEntry] = field(default_factory=list)
    policy:      RawPolicy           = field(default_factory=RawPolicy)
