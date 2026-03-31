from __future__ import annotations

SEVERITY_COLOURS: dict[str, str] = {
    "critical": "#CC1A1A",
    "high": "#E67300",
    "medium": "#E6BF00",
    "low": "#3380CC",
    "info": "#808080",
}


def severity_colour_hex(severity: str) -> str:
    return SEVERITY_COLOURS.get(severity.lower(), SEVERITY_COLOURS["info"])
