from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from backend.services.reporter.models import ParsedFinding, ReproductionPackDraft


def build_reproduction_packs(
    findings: list[ParsedFinding],
) -> tuple[list[ReproductionPackDraft], list[str], bool]:
    packs: list[ReproductionPackDraft] = []
    errors: list[str] = []
    used_fallback = False

    for finding in findings:
        try:
            packs.append(build_pack(finding))
        except Exception as exc:
            errors.append(f"{finding.finding_id}:pack_generation_failed:{exc}")
            packs.append(build_fallback_pack(finding, str(exc)))
            used_fallback = True

    return packs, errors, used_fallback


def build_pack(finding: ParsedFinding) -> ReproductionPackDraft:
    canonical_url = _canonicalize_url(finding.affected_url)
    curl_command = _build_curl_command(canonical_url, finding)
    http_request_raw = _build_http_request_raw(canonical_url, finding)
    browser_steps = _build_browser_steps(canonical_url, finding)
    notes = "Generated from finding metadata using deterministic ordering."

    return ReproductionPackDraft(
        finding_id=finding.finding_id,
        curl_command=curl_command,
        http_request_raw=http_request_raw,
        browser_steps=browser_steps,
        notes=notes,
        is_fallback=False,
    )


def build_fallback_pack(finding: ParsedFinding, reason: str) -> ReproductionPackDraft:
    return ReproductionPackDraft(
        finding_id=finding.finding_id,
        curl_command=(
            "# Reproduction steps could not be auto-generated.\n"
            f"# Affected URL: {finding.affected_url}\n"
            f"# Parameter: {finding.affected_parameter or 'N/A'}\n"
            "# See manual steps below."
        ),
        http_request_raw=(
            "[Not available - pack generation failed]\n"
            f"Reason: {reason}"
        ),
        browser_steps=(
            "1. Open the affected URL in a browser.\n"
            "2. Recreate the request context manually.\n"
            "3. Observe response differences and verify impact."
        ),
        notes=(
            "This reproduction pack was auto-generated as a fallback. "
            "Manual validation is required."
        ),
        is_fallback=True,
    )


def _canonicalize_url(raw_url: str) -> str:
    split = urlsplit(_with_default_scheme(raw_url))
    path = split.path or "/"
    sorted_query = urlencode(sorted(parse_qsl(split.query, keep_blank_values=True)))
    return urlunsplit((split.scheme, split.netloc, path, sorted_query, split.fragment))


def _with_default_scheme(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        return "https://unknown.invalid/"
    split = urlsplit(value)
    if split.scheme:
        return value
    return f"https://{value.lstrip('/')}"


def _build_curl_command(url: str, finding: ParsedFinding) -> str:
    parts = ["curl", "-i", "-sS", f"'{url}'"]
    if finding.affected_parameter:
        parts.append(f"--data-urlencode '{finding.affected_parameter}=<payload>'")
    return " ".join(parts)


def _build_http_request_raw(url: str, finding: ParsedFinding) -> str:
    split = urlsplit(url)
    path = split.path or "/"
    if split.query:
        path = f"{path}?{split.query}"
    lines = [
        f"GET {path} HTTP/1.1",
        f"Host: {split.netloc}",
        "User-Agent: AttackBot-Reporter/1.0",
        "Accept: */*",
    ]
    if finding.affected_parameter:
        lines.append(f"X-AttackBot-Param: {finding.affected_parameter}")
    return "\n".join(lines)


def _build_browser_steps(url: str, finding: ParsedFinding) -> str:
    lines = [
        f"1. Navigate to {url}.",
        "2. Open browser devtools and enable Preserve log.",
        "3. Execute the request while observing network traffic.",
    ]
    if finding.affected_parameter:
        lines.append(f"4. Modify parameter '{finding.affected_parameter}' and repeat.")
    else:
        lines.append("4. Repeat with controlled payload variants.")
    return "\n".join(lines)
