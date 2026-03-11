import ipaddress
import re
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

    Fatal contract: if scope is empty, raise ScanError — never proceed blind.
    """

    def __init__(self, scope: ScopeDefinition) -> None:
        if not scope.in_scope:
            raise ScanError(
                "Scope definition has no in_scope entries — "
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
        # Normalize: strip scheme for domain matching
        domain = self._extract_domain(target)
        ip = self._try_parse_ip(domain)

        if self._matches_any(domain, ip, self._out_of_scope, self._out_networks):
            return False
        return self._matches_any(domain, ip, self._in_scope, self._in_networks)

    def filter_targets(self, targets: list[str]) -> list[str]:
        """Filter a list, keeping only in-scope targets. Logs rejections."""
        in_scope, rejected = [], []
        for t in targets:
            if self.is_in_scope(t):
                in_scope.append(t)
            else:
                rejected.append(t)
        if rejected:
            logger.warning("Out-of-scope targets removed",
                           count=len(rejected), examples=rejected[:5])
        return in_scope

    # ── Private helpers ─────────────────────────────────────────────────

    def _matches_any(
        self,
        domain: str,
        ip: Optional["ipaddress.IPv4Address | ipaddress.IPv6Address"],
        rules: list[str],
        networks: list["ipaddress.IPv4Network | ipaddress.IPv6Network"],
    ) -> bool:
        for rule in rules:
            if self._matches_rule(domain, rule):
                return True
        if ip:
            for net in networks:
                try:
                    if ip in net:
                        return True
                except TypeError:
                    continue
        return False

    @staticmethod
    def _matches_rule(domain: str, rule: str) -> bool:
        """
        Match a domain against a scope rule.
        Supports: exact match, wildcard (*.example.com), URL prefix.
        """
        rule_domain = ScopeFilter._extract_domain(rule)
        if rule_domain.startswith("*."):
            # Wildcard: *.example.com matches sub.example.com but not example.com
            suffix = rule_domain[2:]  # "example.com"
            return domain == suffix or domain.endswith("." + suffix)
        # Exact domain match or URL prefix match
        return domain == rule_domain or domain.endswith("." + rule_domain)

    @staticmethod
    def _extract_domain(target: str) -> str:
        """Extract lowercase hostname from URL or raw domain string."""
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
    def _parse_cidrs(rules: list[str]) -> list["ipaddress.IPv4Network | ipaddress.IPv6Network"]:
        networks = []
        for rule in rules:
            try:
                networks.append(ipaddress.ip_network(rule, strict=False))
            except ValueError:
                pass
        return networks