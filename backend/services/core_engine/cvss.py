from typing import Optional


# Base CVSS scores by severity — conservative defaults for unverified findings
SEVERITY_CVSS_MAP: dict[str, float] = {
    "critical": 9.0,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
    "info": 0.0,
}

# Nuclei severity → our severity label
NUCLEI_SEVERITY_MAP: dict[str, str] = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "unknown": "info",
}

# vuln type → default severity (for scanners that don't emit a severity)
VULN_TYPE_SEVERITY_MAP: dict[str, str] = {
    "xss": "high",
    "reflected_xss": "high",
    "stored_xss": "critical",
    "cors_misconfiguration": "medium",
    "crlf_injection": "medium",
    "js_secret": "high",       # API keys/credentials in JS
    "open_redirect": "medium",
    "sqli": "critical",
    "ssrf": "high",
}


def severity_to_cvss(severity: str) -> float:
    return SEVERITY_CVSS_MAP.get(severity.lower(), 5.0)


def nuclei_severity(raw: str) -> str:
    return NUCLEI_SEVERITY_MAP.get(raw.lower(), "info")


def infer_severity(vulnerability_type: str, raw_severity: Optional[str] = None) -> str:
    if raw_severity:
        normalized = raw_severity.lower()
        if normalized in SEVERITY_CVSS_MAP:
            return normalized
    return VULN_TYPE_SEVERITY_MAP.get(vulnerability_type.lower(), "medium")