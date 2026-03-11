"""
Collector abstraction layer.

BaseCollector defines the interface every platform collector must implement.
CollectorRegistry maps platform name → collector class — add new platforms here only.
"""

from abc import ABC, abstractmethod
from backend.services.scraper.models import RawProgram, Program


class BaseCollector(ABC):
    """
    Abstract base for all platform collectors.
    Each platform implements exactly these three methods.
    No collector should import from another collector.
    """

    @abstractmethod
    def fetch_listing(self) -> list[RawProgram]:
        """
        Fetch the full list of accessible programs from the platform.
        Must handle pagination internally — returns a flat list.
        Must handle 429 internally — raises CollectorRateLimitError after exhausting retries.
        """
        ...

    @abstractmethod
    def fetch_details(self, handle: str) -> RawProgram:
        """
        Fetch full detail for a single program by handle.
        Includes structured scopes and policy data.
        """
        ...

    @abstractmethod
    def normalize(self, raw: RawProgram) -> Program:
        """
        Map the raw platform response to the canonical Program dataclass.
        Must never raise — return a best-effort Program even on partial data.
        """
        ...


class CollectorRegistry:
    """
    Maps platform name → collector class.
    Add new platforms here and nowhere else.

    Registration happens at import time via the self-register pattern:
        CollectorRegistry.register("hackerone", HackerOneCollector)
    """
    _registry: dict[str, type[BaseCollector]] = {}

    @classmethod
    def register(cls, platform: str, collector_cls: type[BaseCollector]) -> None:
        cls._registry[platform] = collector_cls

    @classmethod
    def get(cls, platform: str) -> type[BaseCollector]:
        if platform not in cls._registry:
            raise ValueError(
                f"No collector registered for platform: {platform!r}. "
                f"Registered: {list(cls._registry.keys())}"
            )
        return cls._registry[platform]

    @classmethod
    def all_platforms(cls) -> list[str]:
        return list(cls._registry.keys())