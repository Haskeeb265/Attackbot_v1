"""Unit tests for renderers/theme.py."""

from __future__ import annotations

import pytest

from backend.services.reporter.renderers.theme import severity_colour_hex, SEVERITY_COLOURS


@pytest.mark.parametrize(
    "severity,expected_color",
    [
        ("critical", "#CC1A1A"),
        ("high", "#E67300"),
        ("medium", "#E6BF00"),
        ("low", "#3380CC"),
        ("info", "#808080"),
    ],
)
def test_severity_colour_hex_returns_expected_colors(severity: str, expected_color: str) -> None:
    """Test severity color lookup with standard severity levels."""
    assert severity_colour_hex(severity) == expected_color


def test_severity_colour_hex_fallback_to_info() -> None:
    """Test that unknown severity falls back to info color."""
    assert severity_colour_hex("unknown") == "#808080"
    assert severity_colour_hex("") == "#808080"


def test_severity_colour_hex_case_insensitive() -> None:
    """Test severity color lookup is case insensitive."""
    assert severity_colour_hex("CRITICAL") == "#CC1A1A"
    assert severity_colour_hex("Critical") == "#CC1A1A"
    assert severity_colour_hex("HIGH") == "#E67300"
    assert severity_colour_hex("High") == "#E67300"


def test_severity_colours_contains_all_severities() -> None:
    """Test that SEVERITY_COLOURS contains expected severity levels."""
    expected_severities = {"critical", "high", "medium", "low", "info"}
    assert set(SEVERITY_COLOURS.keys()) == expected_severities
