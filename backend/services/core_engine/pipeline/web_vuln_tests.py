import asyncio
import re
import httpx
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags
from backend.services.core_engine.models import FindingCandidate, DiscoveredEndpoint
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage5")

STAGE_NUMBER = 5.0
STAGE_NAME = "web_vuln_tests"

# Passive checks based on enumerated endpoints (no HTTP requests needed)
SENSITIVE_PATHS = {
    "/.env": ("Exposed environment file", "critical"),
    "/.git/HEAD": ("Exposed Git metadata", "critical"),
    "/.git/config": ("Exposed Git config", "critical"),
}

# XSS probe payloads — reflected only, no stored
XSS_PAYLOADS = [
    '<script>alert(1)</script>',
    '"><img src=x onerror=alert(1)>',
    "';alert(1)//",
]

# CORS test origins
CORS_TEST_ORIGINS = [
    "https://evil.com",
    "null",
    "https://attacker.example.com",
]


async def run(
    ctx: ScanContext,
    endpoints: list[DiscoveredEndpoint],
    scope_filter: ScopeFilter,
    feature_flags: FeatureFlags,
) -> list[FindingCandidate]:
    """
    Stage 5: Targeted web vulnerability tests.
    Always: XSS, CORS.
    Gated: SQLi, SSRF, CRLF (require explicit feature flag).
    """
    candidates: list[FindingCandidate] = []
    in_scope_endpoints = [
        ep for ep in endpoints if scope_filter.is_in_scope(ep.full_url)
    ]

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=False,
        verify=False,
    ) as client:
        tasks = []
        for ep in in_scope_endpoints:
            tasks.append(_test_endpoint(ep, client, feature_flags))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        candidates.extend(result)

    logger.info("Stage 5 complete",
                scan_id=ctx.scan_id,
                findings=len(candidates))
    return candidates


async def _test_endpoint(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
    flags: FeatureFlags,
) -> list[FindingCandidate]:
    findings = []
    findings.extend(_passive_sensitive_path_findings(ep))
    findings.extend(await _test_xss(ep, client))
    findings.extend(await _test_cors(ep, client))
    if flags.crlf:
        findings.extend(await _test_crlf(ep, client))
    # SQLi and SSRF are gated — implement in M6+ or when flags are enabled
    return findings


def _passive_sensitive_path_findings(ep: DiscoveredEndpoint) -> list[FindingCandidate]:
    """
    Create findings for clearly sensitive paths discovered during enumeration.
    Uses `ep.response_code` if present; does not perform an HTTP request.
    """
    if not ep.response_code:
        return []
    title_sev = SENSITIVE_PATHS.get(ep.path)
    if not title_sev:
        return []
    title, severity = title_sev
    # Treat auth-required access as still significant
    if ep.response_code not in {200, 204, 301, 302, 307, 401, 403}:
        return []
    return [
        FindingCandidate(
            vulnerability_type="sensitive_file_exposure",
            title=title,
            severity=severity,
            affected_url=ep.full_url,
            description=f"Sensitive path `{ep.path}` was discovered during enumeration with HTTP {ep.response_code}.",
            source="enumeration_passive",
            reproduction_steps=f"GET {ep.full_url}\nObserve HTTP {ep.response_code}.",
            raw_output={"path": ep.path, "response_code": ep.response_code},
        )
    ]


async def _test_xss(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
) -> list[FindingCandidate]:
    """Test for reflected XSS by injecting payloads into query parameters."""
    findings = []
    params = ep.parameters or {}
    if not params:
        return findings  # No parameters to test

    for param_name in list(params.keys())[:10]:  # cap at 10 params
        for payload in XSS_PAYLOADS:
            test_params = {**params, param_name: payload}
            try:
                resp = await client.get(ep.full_url, params=test_params)
                if payload in resp.text:
                    findings.append(FindingCandidate(
                        vulnerability_type="reflected_xss",
                        title=f"Reflected XSS in parameter '{param_name}'",
                        severity="high",
                        affected_url=ep.full_url,
                        affected_parameter=param_name,
                        payload=payload,
                        description=(
                            f"Reflected XSS detected in parameter '{param_name}'. "
                            f"Payload was reflected verbatim in the response."
                        ),
                        source="xss_scanner",
                        reproduction_steps=(
                            f"GET {ep.full_url}?{param_name}={payload}\n"
                            f"Observe payload in response body."
                        ),
                    ))
                    break  # One finding per parameter is enough
            except Exception:
                continue
    return findings


async def _test_cors(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
) -> list[FindingCandidate]:
    """Test for CORS misconfiguration by varying Origin header."""
    findings = []
    for origin in CORS_TEST_ORIGINS:
        try:
            resp = await client.get(
                ep.full_url,
                headers={"Origin": origin},
            )
            acao = resp.headers.get("access-control-allow-origin", "")
            acac = resp.headers.get("access-control-allow-credentials", "").lower()

            # Misconfig: reflects arbitrary origin + allows credentials
            if (acao == origin or acao == "*") and acac == "true":
                findings.append(FindingCandidate(
                    vulnerability_type="cors_misconfiguration",
                    title="CORS Misconfiguration — Arbitrary Origin with Credentials",
                    severity="high",
                    affected_url=ep.full_url,
                    description=(
                        f"The server reflects the Origin '{origin}' in "
                        f"Access-Control-Allow-Origin and sets "
                        f"Access-Control-Allow-Credentials: true. "
                        f"This allows cross-origin requests with credentials."
                    ),
                    source="cors_scanner",
                    payload=origin,
                    reproduction_steps=(
                        f"curl -H 'Origin: {origin}' {ep.full_url}\n"
                        f"Observe: Access-Control-Allow-Origin: {origin}\n"
                        f"Observe: Access-Control-Allow-Credentials: true"
                    ),
                ))
                break
        except Exception:
            continue
    return findings


async def _test_crlf(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
) -> list[FindingCandidate]:
    """CRLF injection test — gated, only runs when feature flag enabled."""
    findings = []
    payload = "%0d%0aSet-Cookie:crlf=injected"
    try:
        resp = await client.get(f"{ep.full_url}{payload}")
        if "crlf=injected" in str(resp.headers):
            findings.append(FindingCandidate(
                vulnerability_type="crlf_injection",
                title="CRLF Injection",
                severity="medium",
                affected_url=ep.full_url,
                payload=payload,
                description="CRLF injection detected — attacker can inject HTTP headers.",
                source="crlf_scanner",
            ))
    except Exception:
        pass
    return findings