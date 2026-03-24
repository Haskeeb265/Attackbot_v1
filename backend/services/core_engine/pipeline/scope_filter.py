import ipaddress
from typing import Optional
from urllib.parse import urlparse

from backend.services.core_engine.pipeline.context import ScopeDefinition
from backend.shared.exceptions import ScanError
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage0")


class ScopeFilter:
    """
    Evaluates whether a URL, domain, or IP is within the program's declared scope.
    Built once at Stage 0 from the ScopeDefinition in the scan message.

    Fatal contract: if scope is empty, raise ScanError and never proceed blind.
    """

    def __init__(self, scope: ScopeDefinition) -> None:
        if not scope.in_scope:
            raise ScanError(
                "Scope definition has no in_scope entries - "
                "refusing to scan without defined scope."
            )
        self._in_scope = scope.in_scope
        self._out_of_scope = scope.out_of_scope
        self._in_networks = self._parse_cidrs(scope.in_scope)
        self._out_networks = self._parse_cidrs(scope.out_of_scope)
        logger.info(
            "ScopeFilter built",
            in_scope_count=len(self._in_scope),
            out_of_scope_count=len(self._out_of_scope),
        )

    def is_in_scope(self, target: str) -> bool:
        """
        Returns True only if target matches at least one in-scope rule
        and does NOT match any out-of-scope rule.
        Out-of-scope always wins.
        """
        domain = self._extract_domain(target)
        ip = self._try_parse_ip(domain)

        if self._matches_any(domain, ip, self._out_of_scope, self._out_networks):
            return False
        return self._matches_any(domain, ip, self._in_scope, self._in_networks)

    def filter_targets(self, targets: list[str]) -> list[str]:
        """Filter a list, keeping only in-scope targets. Logs rejections."""
        in_scope, rejected = [], []
        for target in targets:
            if self.is_in_scope(target):
                in_scope.append(target)
            else:
                rejected.append(target)
        if rejected:
            logger.warning(
                "Out-of-scope targets removed",
                count=len(rejected),
                examples=rejected[:5],
            )
        return in_scope

    def is_host_in_domain_scope(self, host: str) -> bool:
        """
        Domain/wildcard-only scope check for hostnames.

        Used by Stage 1 seed admission for asset_type=url so URL seed matching
        reuses the same domain and wildcard behavior as scope filtering.
        """
        domain = self._extract_domain(host)
        if not domain:
            return False
        if self._matches_any_domain_rule(domain, self._out_of_scope):
            return False
        return self._matches_any_domain_rule(domain, self._in_scope)

    def _matches_any(
        self,
        domain: str,
        ip: Optional["ipaddress.IPv4Address | ipaddress.IPv6Address"],
        rules: list[str] | list[dict],
        networks: list["ipaddress.IPv4Network | ipaddress.IPv6Network"],
    ) -> bool:
        for rule in rules:
            if self._matches_rule(domain, rule):
                return True
        if ip:
            for network in networks:
                try:
                    if ip in network:
                        return True
                except TypeError:
                    continue
        return False

    def _matches_any_domain_rule(self, domain: str, rules: list[str] | list[dict]) -> bool:
        for rule in rules:
            asset_type, rule_value = self._coerce_rule(rule)
            if not self._is_domain_rule(asset_type, rule_value):
                continue
            if self._matches_rule(domain, rule):
                return True
        return False

    @staticmethod
    def _matches_rule(domain: str, rule: str | dict) -> bool:
        """
        Match a domain against a scope rule.

        Supports exact match, wildcard (*.example.com), and domain-root rules
        (domain + subdomains) for API-style scope entries.
        """
        asset_type, rule_value = ScopeFilter._coerce_rule(rule)
        rule_str = rule_value.strip()
        rule_domain = ScopeFilter._extract_domain(rule)
        if not rule_domain:
            return False

        if asset_type == "wildcard_domain":
            # Wildcard asset type: always subdomains-only, even if value lacks "*." prefix.
            return domain.endswith("." + rule_domain)

        if rule_str.startswith("*."):
            # Wildcard: *.example.com matches sub.example.com only.
            return domain.endswith("." + rule_domain)

        if asset_type == "domain":
            # Root domain rule from API: include root and all subdomains.
            return domain == rule_domain or domain.endswith("." + rule_domain)

        # Plain string fallback: exact host match.
        return domain == rule_domain

    @staticmethod
    def _extract_domain(target: str | dict) -> str:
        """Extract lowercase hostname from URL/dict/raw host string."""
        if hasattr(target, "value"):
            target = getattr(target, "value", "")
        if isinstance(target, dict):
            target = str(target.get("value") or target.get("url") or "")
        if not isinstance(target, str):
            target = str(target)

        if "://" in target:
            parsed = urlparse(target)
            host = parsed.hostname or ""
        else:
            host = target.split("/")[0].split(":")[0]
        return host.lower().lstrip("*.")

    @staticmethod
    def _try_parse_ip(value: str) -> Optional["ipaddress.IPv4Address | ipaddress.IPv6Address"]:
        try:
            return ipaddress.ip_address(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_cidrs(rules: list[str] | list[dict]) -> list["ipaddress.IPv4Network | ipaddress.IPv6Network"]:
        networks = []
        for rule in rules:
            _, rule_value = ScopeFilter._coerce_rule(rule)
            try:
                networks.append(ipaddress.ip_network(rule_value, strict=False))
            except ValueError:
                pass
        return networks

    @staticmethod
    def _coerce_rule(rule: object) -> tuple[str | None, str]:
        if isinstance(rule, dict):
            return rule.get("asset_type"), str(rule.get("value") or rule.get("url") or "")
        if hasattr(rule, "value"):
            return getattr(rule, "asset_type", None), str(getattr(rule, "value", "") or "")
        return None, str(rule or "")

    @staticmethod
    def _is_domain_rule(asset_type: str | None, rule_value: str) -> bool:
        if asset_type in {"domain", "wildcard_domain"}:
            return True
        if asset_type in {"url", "ip_range", "mobile_app", "api"}:
            return False

        # Legacy string-only rules: allow host-like values, exclude CIDRs.
        candidate = (rule_value or "").strip()
        if not candidate:
            return False
        try:
            ipaddress.ip_network(candidate, strict=False)
            return False
        except ValueError:
            pass
        return bool(ScopeFilter._extract_domain(candidate))
