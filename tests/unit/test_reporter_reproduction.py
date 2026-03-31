from uuid import uuid4

from backend.services.reporter.models import ParsedFinding
from backend.services.reporter.reproduction import (
    build_fallback_pack,
    build_pack,
    build_reproduction_packs,
)


def _finding(**overrides) -> ParsedFinding:
    payload = {
        "finding_id": uuid4(),
        "title": "Reflected XSS",
        "vulnerability_type": "xss",
        "severity": "high",
        "cvss_score": 7.5,
        "cvss_vector": None,
        "affected_url": "https://example.com/search?b=2&a=1",
        "affected_parameter": "q",
        "description": "desc",
        "reproduction_steps": None,
        "source": "unit",
        "is_verified": False,
        "raw_output": None,
    }
    payload.update(overrides)
    return ParsedFinding(**payload)


def test_build_pack_is_deterministic_for_query_order() -> None:
    finding = _finding(affected_url="https://example.com/search?z=9&a=1")
    pack = build_pack(finding)

    assert "a=1&z=9" in pack.curl_command
    assert pack.is_fallback is False


def test_build_fallback_pack_contains_required_marker() -> None:
    finding = _finding()
    pack = build_fallback_pack(finding, "boom")

    assert pack.is_fallback is True
    assert "auto-generated as a fallback" in (pack.notes or "")
    assert "Not available - pack generation failed" in pack.http_request_raw


def test_build_reproduction_packs_uses_fallback_on_error(monkeypatch) -> None:
    finding = _finding()

    def _explode(_finding_obj):
        raise RuntimeError("forced")

    monkeypatch.setattr("backend.services.reporter.reproduction.build_pack", _explode)

    packs, errors, used_fallback = build_reproduction_packs([finding])

    assert len(packs) == 1
    assert used_fallback is True
    assert packs[0].is_fallback is True
    assert errors and "pack_generation_failed" in errors[0]
