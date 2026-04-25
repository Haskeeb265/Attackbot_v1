from __future__ import annotations

from unittest.mock import patch
from unittest import mock
from uuid import uuid4

import aiobreaker
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timezone


_OriginalCircuitBreakerError = aiobreaker.CircuitBreakerError


class _CompatCircuitBreakerError(_OriginalCircuitBreakerError):
    def __init__(self, message: str, reopen_time: datetime | None = None) -> None:
        if reopen_time is None:
            reopen_time = datetime.now(timezone.utc)
        super().__init__(message, reopen_time)


aiobreaker.CircuitBreakerError = _CompatCircuitBreakerError


class _MiniMocker:
    AsyncMock = mock.AsyncMock

    def patch(self, target: str, **kwargs: object):
        return patch(target, **kwargs)


@pytest.fixture(scope="function")
def mocker() -> _MiniMocker:
    return _MiniMocker()


class _FakeExchange:
    async def publish(self, message: object, routing_key: str) -> None:
        _ = message
        _ = routing_key


class _FakeChannel:
    def __init__(self) -> None:
        self.default_exchange = _FakeExchange()

    async def close(self) -> None:
        return None


class _FakeRabbitMQClient:
    url = "amqp://fake-rabbitmq"

    async def get_channel(self) -> _FakeChannel:
        return _FakeChannel()


@pytest_asyncio.fixture(scope="function")
async def rabbitmq_client() -> _FakeRabbitMQClient:
    return _FakeRabbitMQClient()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncClient:
    from backend.services.core_engine.main import app

    with (
        patch("backend.services.core_engine.main.check_db_health", return_value=True),
        patch("backend.services.core_engine.main.check_rabbitmq_health", return_value=True),
        patch("backend.services.core_engine.main.check_storage_health", return_value=True),
        patch("backend.services.core_engine.main._check_scraper_health", return_value=True),
        patch("backend.services.core_engine.main._reserve_scan_id", return_value=str(uuid4())),
        patch("backend.services.core_engine.main._enqueue_scan", return_value=None),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
            yield test_client
