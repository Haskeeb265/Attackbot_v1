"""
Scope parser — validates and normalizes ProgramScope objects.

The scope parser is a thin validation + normalization layer that sits between
the collector's normalize() output and the repository upsert.

Most work is done by the collector using structured_scopes. This parser:
1. Strips whitespace from values
2. Drops empty entries with a warning
3. Re-infers asset_type if the collector produced a mismatch (API sometimes returns wrong types)
"""

import re
from backend.services.scraper.models import ProgramScope
from backend.shared.logging import get_logger

log = get_logger(__name__)

# Regex for CIDR notation (IPv4 and IPv6)
CIDR_PATTERN = re.compile(
    r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'        # IPv4 CIDR
    r'|^[0-9a-fA-F:]+/\d{1,3}$'               # IPv6 CIDR
)

# Wildcard domain: starts with *.
WILDCARD_PATTERN = re.compile(r'^\*\.')

# Domain: no scheme, no wildcard, no path
DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]+[a-zA-Z0-9]$')

# URL: has http(s) scheme
URL_PATTERN = re.compile(r'^https?://')

# Mobile app bundle identifier (com.example.app or reverse-DNS format)
MOBILE_BUNDLE_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*){2,}$')


class ScopeParser:
    """
    Validates and normalizes ProgramScope objects.

    Input:  list of ProgramScope from collector's normalize()
    Output: list of validated ProgramScope (invalid entries logged + dropped)
    """

    def parse(self, scopes: list[ProgramScope]) -> list[ProgramScope]:
        """Validate and clean all scope entries. Drops invalid entries with a warning."""
        result = []
        for scope in scopes:
            cleaned = self._validate_and_clean(scope)
            if cleaned is not None:
                result.append(cleaned)
        return result

    def _validate_and_clean(self, scope: ProgramScope) -> ProgramScope | None:
        value = scope.value.strip()

        if not value:
            log.warning("scope_empty_value_dropped", scope_type=scope.scope_type)
            return None

        # Re-infer asset_type from value if the collector produced a mismatch
        # Catches cases where the API returns wrong asset_type
        inferred = self._infer_asset_type(value)
        if inferred != scope.asset_type:
            log.debug(
                "scope_asset_type_corrected",
                original=scope.asset_type,
                inferred=inferred,
                value=value,
            )

        return ProgramScope(
            scope_type=scope.scope_type,
            asset_type=inferred,
            value=value,
            notes=scope.notes,
        )

    def _infer_asset_type(self, value: str) -> str:
        """Best-effort asset type inference from the value string."""
        if CIDR_PATTERN.match(value):
            return "ip_range"
        if WILDCARD_PATTERN.match(value):
            return "wildcard_domain"
        if URL_PATTERN.match(value):
            return "url"
        if MOBILE_BUNDLE_PATTERN.match(value) and value.count('.') >= 2:
            # Mobile bundle IDs have 3+ components starting with a known TLD prefix
            parts = value.split('.')
            if parts[0] in ('com', 'org', 'io', 'net', 'app'):
                return "mobile_app"
        if DOMAIN_PATTERN.match(value):
            return "domain"
        # Default: anything with a slash is treated as a URL path
        if '/' in value:
            return "url"
        return "domain"