"""
Unit tests for ScopeParser.

Tests cover all asset types, normalisation edge cases, filtering,
and value-based type inference.
"""
import pytest

from backend.services.scraper.collectors.models import RawScopeEntry
from backend.services.scraper.scope_parser import ScopeParser


@pytest.fixture
def parser() -> ScopeParser:
    return ScopeParser()


def make_entry(
    asset_type: str,
    value: str,
    scope_type: str = "in_scope",
    notes: str = "",
) -> RawScopeEntry:
    return RawScopeEntry(
        asset_type=asset_type,
        value=value,
        scope_type=scope_type,
        notes=notes,
    )


# ── Wildcard domain ────────────────────────────────────────────────────

def test_wildcard_preserved(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("wildcard_domain", "*.example.com")])
    assert len(entries) == 1
    assert entries[0].value      == "*.example.com"
    assert entries[0].asset_type == "wildcard_domain"


def test_dot_prefix_normalised_to_wildcard(parser: ScopeParser) -> None:
    """.example.com → *.example.com"""
    entries = parser.parse_all([make_entry("wildcard_domain", ".example.com")])
    assert entries[0].value == "*.example.com"


def test_wildcard_lowercased(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("wildcard_domain", "*.EXAMPLE.COM")])
    assert entries[0].value == "*.example.com"


def test_wildcard_inferred_from_value(parser: ScopeParser) -> None:
    """A value starting with '*.' should be detected as wildcard_domain even with unknown type."""
    entries = parser.parse_all([make_entry("OTHER_UNKNOWN", "*.api.example.com")])
    assert len(entries) == 1
    assert entries[0].asset_type == "wildcard_domain"
    assert entries[0].value      == "*.api.example.com"


# ── CIDR / IP ──────────────────────────────────────────────────────────

def test_cidr_range_preserved(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("ip_range", "10.0.0.0/24")])
    assert entries[0].value      == "10.0.0.0/24"
    assert entries[0].asset_type == "ip_range"


def test_host_cidr_reduced_to_ip(parser: ScopeParser) -> None:
    """/32 CIDR should be reduced to the bare host IP."""
    entries = parser.parse_all([make_entry("ip_range", "192.168.1.100/32")])
    assert entries[0].value == "192.168.1.100"


def test_ip_address_inferred(parser: ScopeParser) -> None:
    """A bare IP address should be detected as ip_range."""
    entries = parser.parse_all([make_entry("unknown_type", "10.0.0.1")])
    assert entries[0].asset_type == "ip_range"


def test_cidr_inferred(parser: ScopeParser) -> None:
    """A CIDR string should be detected as ip_range via inference."""
    entries = parser.parse_all([make_entry("OTHER", "192.168.0.0/16")])
    assert entries[0].asset_type == "ip_range"


# ── URL ────────────────────────────────────────────────────────────────

def test_url_trailing_slash_stripped(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("url", "https://api.example.com/")])
    assert entries[0].value == "https://api.example.com"


def test_url_trailing_slash_preserved_if_none(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("url", "https://api.example.com")])
    assert entries[0].value == "https://api.example.com"


def test_url_inferred_from_https_prefix(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("OTHER", "https://api.example.com")])
    assert entries[0].asset_type == "url"


def test_url_inferred_from_http_prefix(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("OTHER", "http://internal.example.com")])
    assert entries[0].asset_type == "url"


# ── Domain ─────────────────────────────────────────────────────────────

def test_domain_lowercased(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("domain", "API.Example.COM")])
    assert entries[0].value == "api.example.com"


def test_domain_trailing_dot_removed(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("domain", "example.com.")])
    assert entries[0].value == "example.com"


def test_domain_inferred_from_value_shape(parser: ScopeParser) -> None:
    """A value that looks like a domain should be detected as such."""
    entries = parser.parse_all([make_entry("UNKNOWN", "sub.example.com")])
    assert entries[0].asset_type == "domain"


# ── Mobile app ─────────────────────────────────────────────────────────

def test_mobile_app_preserved(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("mobile_app", "com.example.myapp")])
    assert entries[0].asset_type == "mobile_app"
    assert entries[0].value      == "com.example.myapp"


def test_android_package_inferred(parser: ScopeParser) -> None:
    """Android reverse-domain package names should be detected as mobile_app."""
    entries = parser.parse_all([make_entry("OTHER", "com.example.android")])
    assert entries[0].asset_type == "mobile_app"


# ── Out of scope ───────────────────────────────────────────────────────

def test_out_of_scope_scope_type_preserved(parser: ScopeParser) -> None:
    entries = parser.parse_all([
        make_entry("domain", "admin.example.com", scope_type="out_of_scope")
    ])
    assert len(entries) == 1
    assert entries[0].scope_type == "out_of_scope"
    assert entries[0].value      == "admin.example.com"


# ── Edge cases ─────────────────────────────────────────────────────────

def test_empty_value_filtered_out(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("domain", "   ")])
    assert entries == []


def test_empty_value_empty_string_filtered(parser: ScopeParser) -> None:
    entries = parser.parse_all([make_entry("url", "")])
    assert entries == []


def test_unrecognised_type_with_unrecognisable_value_filtered(
    parser: ScopeParser,
) -> None:
    """A value that cannot be inferred and has an unknown type should be filtered out."""
    entries = parser.parse_all([make_entry("COMPLETELY_UNKNOWN", "not-a-valid-value!!!")])
    assert entries == []


def test_mixed_valid_and_invalid_entries(parser: ScopeParser) -> None:
    """Valid entries pass through; invalid ones are silently filtered."""
    raw = [
        make_entry("domain", "valid.com"),
        make_entry("domain", ""),          # filtered — empty
        make_entry("url", "https://ok.com"),
        make_entry("ip_range", "10.0.0.0/8"),
    ]
    parsed = parser.parse_all(raw)
    assert len(parsed) == 3


def test_notes_preserved(parser: ScopeParser) -> None:
    entries = parser.parse_all([
        make_entry("domain", "example.com", notes="Main production domain")
    ])
    assert entries[0].notes == "Main production domain"


def test_parse_all_empty_list(parser: ScopeParser) -> None:
    assert parser.parse_all([]) == []


def test_multiple_scope_types(parser: ScopeParser) -> None:
    """parse_all handles a mix of in_scope and out_of_scope entries."""
    raw = [
        make_entry("wildcard_domain", "*.example.com", scope_type="in_scope"),
        make_entry("domain", "admin.example.com",     scope_type="out_of_scope"),
    ]
    parsed = parser.parse_all(raw)
    in_scope  = [p for p in parsed if p.scope_type == "in_scope"]
    out_scope = [p for p in parsed if p.scope_type == "out_of_scope"]
    assert len(in_scope)  == 1
    assert len(out_scope) == 1
