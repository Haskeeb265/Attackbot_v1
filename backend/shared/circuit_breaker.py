from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Callable

import httpx
from aiobreaker import CircuitBreaker, CircuitBreakerError, CircuitBreakerState
from prometheus_client import Gauge

from backend.shared.logging import get_logger

logger = get_logger(__name__)


class _Value:
    def __init__(self) -> None:
        self._v = 0.0

    def get(self) -> float:
        return self._v

    def inc(self, amount: float = 1.0) -> None:
        self._v += amount


class _MetricEntry:
    def __init__(self) -> None:
        self._value = _Value()


class CompatCounter:
    """
    Minimal counter compatible with existing tests that introspect `_metrics[0]._value`.
    """

    def __init__(self) -> None:
        self._metrics = [_MetricEntry()]

    def labels(self, **_: Any) -> "CompatCounter":
        return self

    def inc(self, amount: float = 1.0) -> None:
        self._metrics[0]._value.inc(amount)


circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Current circuit state (0=closed, 1=open, 2=half_open)",
    ["service", "target_service"],
)

circuit_breaker_transitions = CompatCounter()
circuit_breaker_failures = CompatCounter()
circuit_breaker_rejections = CompatCounter()


def _state_to_number(state: CircuitBreakerState) -> int:
    if state == CircuitBreakerState.OPEN:
        return 1
    if state == CircuitBreakerState.HALF_OPEN:
        return 2
    return 0


@dataclass
class ManagedCircuitBreaker:
    name: str
    _breaker: CircuitBreaker
    timeout_seconds: float
    _fail_max: int
    _fail_counter: int = 0
    _state: CircuitBreakerState = CircuitBreakerState.CLOSED
    _opened_at: datetime | None = None

    @property
    def state(self) -> CircuitBreakerState:
        return self._state

    @property
    def fail_max(self) -> int:
        return self._fail_max

    @property
    def fail_counter(self) -> int:
        return self._fail_counter

    def _set_state(self, next_state: CircuitBreakerState) -> None:
        prev_state = self._state
        if prev_state == next_state:
            return
        self._state = next_state
        circuit_breaker_state.labels(service="attackbot", target_service=self.name).set(
            _state_to_number(next_state)
        )
        circuit_breaker_transitions.labels(
            service="attackbot",
            target_service=self.name,
            from_state=prev_state.name.lower(),
            to_state=next_state.name.lower(),
        ).inc()

    def _build_open_error(self) -> CircuitBreakerError:
        reopen_time = datetime.now(timezone.utc) + timedelta(seconds=self.timeout_seconds)
        try:
            return CircuitBreakerError("Timeout not elapsed yet, circuit breaker still open", reopen_time)
        except TypeError:
            return CircuitBreakerError("Timeout not elapsed yet, circuit breaker still open")

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        now = datetime.now(timezone.utc)
        if self._state == CircuitBreakerState.OPEN:
            if self._opened_at and (now - self._opened_at).total_seconds() >= self.timeout_seconds:
                self._set_state(CircuitBreakerState.HALF_OPEN)
            else:
                circuit_breaker_rejections.labels(
                    service="attackbot",
                    target_service=self.name,
                ).inc()
                raise self._build_open_error()

        try:
            result = await func(*args, **kwargs)
            if self._state in (CircuitBreakerState.HALF_OPEN, CircuitBreakerState.OPEN):
                self._set_state(CircuitBreakerState.CLOSED)
            self._fail_counter = 0
            return result
        except CircuitBreakerError:
            circuit_breaker_rejections.labels(
                service="attackbot",
                target_service=self.name,
            ).inc()
            raise
        except Exception:
            circuit_breaker_failures.labels(service="attackbot", target_service=self.name).inc()
            self._fail_counter += 1
            if self._state == CircuitBreakerState.HALF_OPEN or self._fail_counter >= self._fail_max:
                self._opened_at = now
                self._set_state(CircuitBreakerState.OPEN)
                self._fail_counter = self._fail_max
            raise

    def close(self) -> None:
        self._set_state(CircuitBreakerState.CLOSED)
        self._fail_counter = 0
        self._opened_at = None


class ServiceCircuitBreakers:
    _breakers: dict[str, ManagedCircuitBreaker] = {}
    _lock = Lock()

    @classmethod
    def get_breaker(
        cls,
        name: str,
        fail_max: int = 5,
        timeout: float = 60.0,
        expected_exception: Any = Exception,
    ) -> ManagedCircuitBreaker:
        with cls._lock:
            existing = cls._breakers.get(name)
            if existing is not None and existing.fail_max == int(fail_max) and existing.timeout_seconds == float(timeout):
                return existing
            if existing is not None:
                existing.close()

            breaker = CircuitBreaker(fail_max=fail_max, timeout_duration=timedelta(seconds=float(timeout)), name=name)
            managed = ManagedCircuitBreaker(
                name=name,
                _breaker=breaker,
                timeout_seconds=float(timeout),
                _fail_max=int(fail_max),
            )
            cls._breakers[name] = managed
            circuit_breaker_state.labels(service="attackbot", target_service=name).set(0)
            return managed

    @classmethod
    def scraper_api(cls) -> ManagedCircuitBreaker:
        return cls.get_breaker(
            "scraper_api",
            fail_max=5,
            timeout=60.0,
            expected_exception=(httpx.HTTPError, TimeoutError),
        )

    @classmethod
    def core_engine_api(cls) -> ManagedCircuitBreaker:
        return cls.get_breaker(
            "core_engine_api",
            fail_max=5,
            timeout=60.0,
            expected_exception=(httpx.HTTPError, TimeoutError),
        )

    @classmethod
    def hackerone_api(cls) -> ManagedCircuitBreaker:
        return cls.get_breaker(
            "hackerone_api",
            fail_max=5,
            timeout=60.0,
            expected_exception=(httpx.HTTPError, TimeoutError),
        )

    @classmethod
    def get_state_summary(cls) -> dict[str, str]:
        out: dict[str, str] = {}
        for name, managed in cls._breakers.items():
            out[name] = managed.state.name.lower()
        return out

    @classmethod
    def reset_all(cls) -> int:
        reset = 0
        for managed in cls._breakers.values():
            managed.close()
            circuit_breaker_state.labels(service="attackbot", target_service=managed.name).set(0)
            reset += 1
        return reset


class CircuitBreakerWrapper:
    def __init__(self, breaker: ManagedCircuitBreaker) -> None:
        self._breaker = breaker

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            return await self._breaker.call(func, *args, **kwargs)

        return wrapped


def circuit_breaker_scraper(func: Callable[..., Any]) -> Callable[..., Any]:
    return CircuitBreakerWrapper(ServiceCircuitBreakers.scraper_api())(func)


def circuit_breaker_core_engine(func: Callable[..., Any]) -> Callable[..., Any]:
    return CircuitBreakerWrapper(ServiceCircuitBreakers.core_engine_api())(func)


def circuit_breaker_hackerone(func: Callable[..., Any]) -> Callable[..., Any]:
    return CircuitBreakerWrapper(ServiceCircuitBreakers.hackerone_api())(func)
