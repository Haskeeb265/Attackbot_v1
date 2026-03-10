"""
AttackBot scope parser.

Validates and normalises raw scope entries from any platform collector.
Produces typed ParsedScope objects suitable for DB insertion.

Design principles:
  - Filters invalid entries individually rather than failing the whole program
  - Falls back to value-based type inference if asset_type is unrecognised
  - Normalises values consistently (lowercase domains, stripped slashes, etc.)
"""
import ipaddress
import re
from dataclasses import dataclass
from typing import Literal

from shared.logging import get_logger
from .collectors.models import RawScopeEntry

log = get_logger(__name__)

# Canonical type literals used in program_scopes.asset_type
ScopeType      = Literal["in_scope", "out_of_scope"]
ScopeAssetType = Literal["url", "domain", "wildcard_domain", "ip_range", "mobile_app", "api"]

VALID_ASSET_TYPES: set[str] = {
    "url", "domain", "wildcard_domain", "ip_range", "mobile_app", "api"
}


@dataclass
class ParsedScope:
    """A validated, normalised scope entry ready for DB insertion."""
    scope_type: str   # 'in_scope' | 'out_of_scope'
    asset_type: str   # one of VALID_ASSET_TYPES
    value:      str
    notes:      str = ""


class ScopeParser:
    """
    Validates and normalises raw scope entries from any platform collector.

    Filters entries with empty or malformed values rather than failing the
    entire program — a bad single scope entry must not block a valid program.
    """

    def parse_all(self, raw_entries: list[RawScopeEntry]) -> list[ParsedScope]:
        """Parse all raw entries, silently filtering invalid ones."""
        parsed: list[ParsedScope] = []
        for entry in raw_entries:
            result = self._parse_entry(entry)
            if result is not None:
                parsed.append(result)
        return parsed

    def _parse_entry(self, entry: RawScopeEntry) -> ParsedScope | None:
        value = entry.value.strip()
        if not value:
            log.warning("scope_entry_empty_value", asset_type=entry.asset_type)
            return None

        asset_type = self._detect_asset_type(entry.asset_type, value)
        if asset_type is None:
            log.warning("scope_entry_unrecognised",
                        value=value, raw_type=entry.asset_type)
            return None

        normalised_value = self._normalise_value(asset_type, value)

        return ParsedScope(
            scope_type = entry.scope_type,
            asset_type = asset_type,
            value      = normalised_value,
            notes      = entry.notes,
        )

    # ── Type detection ─────────────────────────────────────────────

    def _detect_asset_type(self, raw_type: str, value: str) -> str | None:
        """
        Return the canonical asset type.
        Trusts the collector mapping first; falls back to value-based inference.
        Returns None if the type cannot be determined.
        """
        if raw_type in VALID_ASSET_TYPES:
            return raw_type

        # Value-based inference (fallback for unknown/unmapped types)
        if value.startswith("*.") or value.startswith("."):
            return "wildcard_domain"
        if value.startswith("http://") or value.startswith("https://"):
            return "url"
        if self._is_cidr(value) or self._is_ip(value):
            return "ip_range"
        # Android: com.example.app / io.example.app
        if re.match(r"^(com|io|org|net|co)\.[a-zA-Z0-9]", value):
            return "mobile_app"
        # Looks like a domain: example.com, sub.example.com
        if re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$", value):
            return "domain"

        return None

    # ── Value normalisation ────────────────────────────────────────

    def _normalise_value(self, asset_type: str, value: str) -> str:
        """Apply type-specific normalisation to a scope value."""
        if asset_type == "wildcard_domain":
            # Normalise .example.com → *.example.com
            if value.startswith(".") and not value.startswith("*."):
                value = f"*{value}"
            return value.lower()

        if asset_type == "domain":
            return value.rstrip(".").lower()

        if asset_type == "url":
            return value.rstrip("/")

        if asset_type == "ip_range":
            return self._normalise_cidr(value)

        return value

    # ── IP / CIDR helpers ──────────────────────────────────────────

    @staticmethod
    def _is_cidr(value: str) -> bool:
        try:
            ipaddress.ip_network(value, strict=False)
            return "/" in value  # bare IPs handled by _is_ip
        except ValueError:
            return False

    @staticmethod
    def _is_ip(value: str) -> bool:
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _normalise_cidr(value: str) -> str:
        try:
            net = ipaddress.ip_network(value, strict=False)
            if net.prefixlen == 32:
                return str(net.network_address)
            return str(net)
        except ValueError:
            return value
