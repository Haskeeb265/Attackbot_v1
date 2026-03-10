"""
Base collector abstraction and registry.
Each platform (HackerOne, BugCrowd, etc.) implements BaseCollector.
CollectorRegistry maps platform names to collector classes.
"""
from abc import ABC, abstractmethod
from typing import Any

from shared.logging import get_logger
from shared.exceptions import CollectorError
from .models import RawProgram

log = get_logger(__name__)

# Global registry: platform_name → collector class
_registry: dict[str, type["BaseCollector"]] = {}


def register(platform: str):
    """
    Class decorator to register a collector for a platform.

    Usage:
        @register("hackerone")
        class HackerOneCollector(BaseCollector): ...
    """
    def decorator(cls: type["BaseCollector"]):
        _registry[platform] = cls
        log.info("collector_registered", platform=platform, cls=cls.__name__)
        return cls
    return decorator


def get_collector(platform: str, **kwargs) -> "BaseCollector":
    """
    Instantiate a collector for the given platform.
    Raises CollectorError if the platform is not registered.
    """
    if platform not in _registry:
        raise CollectorError(
            f"No collector registered for platform: {platform!r}. "
            f"Available: {list(_registry.keys())}"
        )
    return _registry[platform](**kwargs)


def available_platforms() -> list[str]:
    """Return all registered platform names."""
    return list(_registry.keys())


class BaseCollector(ABC):
    """
    Platform-agnostic collector interface.

    Subclasses must implement all three methods.
    The contract:
      1. fetch_listing()  — returns the full program list (handles pagination internally)
      2. fetch_details()  — enriches one program with structured scopes
      3. normalize()      — maps RawProgram to the programs table dict schema
    """

    @abstractmethod
    async def fetch_listing(self) -> list[RawProgram]:
        """
        Fetch the full program listing from the platform.
        Must handle pagination internally.
        Must handle rate limiting internally (429 + Retry-After).
        Returns a list of RawProgram — one per program.
        Skips programs that fail individually rather than aborting the full run.
        """
        ...

    @abstractmethod
    async def fetch_details(self, handle: str) -> RawProgram:
        """
        Fetch full program detail including structured scopes.
        Called per-program from fetch_listing().
        May raise CollectorError if the program is not found.
        """
        ...

    @abstractmethod
    def normalize(self, raw: RawProgram) -> dict[str, Any]:
        """
        Map a RawProgram to a dict matching the programs table schema.
        Returns a plain dict — not an ORM model.
        This is the canonical transform; all DB writes go through here.
        """
        ...
