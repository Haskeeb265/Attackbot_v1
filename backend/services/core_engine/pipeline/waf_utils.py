from collections.abc import Iterable

# Keep detection consistent across stages.
WAF_KEYWORDS: tuple[str, ...] = (
    "waf",
    "cloudflare",
    "akamai",
    "f5",
    "sucuri",
    "imperva",
    "barracuda",
    "fortiweb",
)


def detect_waf_technology(technologies: Iterable[object]) -> str | None:
    for tech in technologies:
        name = tech.get("name", "") if isinstance(tech, dict) else str(tech)
        lowered = name.lower()
        if any(keyword in lowered for keyword in WAF_KEYWORDS):
            return name
    return None
