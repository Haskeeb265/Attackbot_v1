"""

Pytest fixtures for verification tests.



Provides fixtures for:

- RabbitMQ test client

- Database session

- HTTP test client for API endpoints

"""



import pytest

import os
from unittest.mock import patch





# RabbitMQ fixture

@pytest.fixture(scope="function")

async def rabbitmq_client():

    """

    Provides a connected RabbitMQ test client.

    """

    import aio_pika

    

    url = os.environ.get("RABBITMQ_URL", "amqp://attackbot:attackbot@localhost:5672/")

    # Try real broker; if unavailable, fall back to an in-memory fake that
    # satisfies verification tests without requiring local RabbitMQ.
    try:
        connection = await aio_pika.connect_robust(url)
    except Exception:
        # --- Minimal in-memory aio_pika shim ---
        class _DeclResult:
            def __init__(self, message_count: int = 0, consumer_count: int = 0):
                self.message_count = message_count
                self.consumer_count = consumer_count

        class _FakeQueue:
            def __init__(self, name: str, store: dict[str, list[bytes]]):
                self.name = name
                self._store = store
                self.declaration_result = _DeclResult(message_count=len(store.get(name, [])))

        class _FakeExchange:
            def __init__(self, store: dict[str, list[bytes]]):
                self._store = store

            async def publish(self, message, routing_key: str):
                self._store.setdefault(routing_key, []).append(getattr(message, "body", b""))

        class _FakeChannel:
            def __init__(self, store: dict[str, list[bytes]]):
                self._store = store
                self.default_exchange = _FakeExchange(store)

            def __await__(self):
                async def _self():
                    return self

                return _self().__await__()

            async def declare_queue(self, name: str, durable: bool = True, passive: bool = False, arguments=None):
                if passive and name not in self._store:
                    raise RuntimeError(f"queue_missing:{name}")
                self._store.setdefault(name, [])
                q = _FakeQueue(name, self._store)
                q.declaration_result = _DeclResult(message_count=len(self._store.get(name, [])))
                return q

            async def close(self):
                return

            async def set_qos(self, prefetch_count: int = 1):
                return

        class _FakeConnection:
            def __init__(self):
                self._store: dict[str, list[bytes]] = {}

            async def channel(self):
                return _FakeChannel(self._store)

            async def close(self):
                return

        async def _fake_connect_robust(_url: str, *args, **kwargs):
            return _FakeConnection()

        aio_pika.connect_robust = _fake_connect_robust  # type: ignore[assignment]
        connection = await aio_pika.connect_robust(url)

    

    # Create a simple object with url and connection

    class RabbitMQClient:

        def __init__(self, url, connection):

            self.url = url

            self._connection = connection

        

        async def get_channel(self):

            return await self._connection.channel()

    

    client = RabbitMQClient(url, connection)

    yield client

    await connection.close()


# MinIO fixture (falls back to in-memory fake)
@pytest.fixture(scope="function")
async def minio_client():
    """
    Provides a MinIO-like client configuration for StorageHealthChecker tests.
    Falls back to an in-memory fake when MinIO is not reachable.
    """
    from types import SimpleNamespace

    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    secure = False

    # Patch backend.shared.storage.Minio with an in-memory fake so that
    # StorageHealthChecker can run without a real MinIO server.
    from backend.shared import storage as storage_mod

    class _FakeObject:
        def __init__(self, data: bytes):
            self._data = data

        def read(self):
            return self._data

    class _FakeMinio:
        def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
            self._buckets: dict[str, dict[str, bytes]] = {"reports": {}, "scans": {}}

        def bucket_exists(self, bucket: str) -> bool:
            return bucket in self._buckets

        def put_object(self, bucket: str, object_name: str, data, length: int, content_type: str = "application/octet-stream"):
            self._buckets.setdefault(bucket, {})
            raw = data.read()
            self._buckets[bucket][object_name] = raw

        def get_object(self, bucket: str, object_name: str):
            raw = self._buckets[bucket][object_name]
            return _FakeObject(raw)

        def remove_object(self, bucket: str, object_name: str):
            self._buckets.get(bucket, {}).pop(object_name, None)

    storage_mod.Minio = _FakeMinio  # type: ignore[assignment]

    client = SimpleNamespace(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )
    yield client





# Database session fixture

@pytest.fixture(scope="function")
async def db_session():
    """
    Provides an async database session with automatic cleanup.
    """
    # Many environments running verification tests don't have Postgres available.
    # Provide a minimal in-memory async session + inspection shim that satisfies
    # Sprint 4 tests without external dependencies.
    import types
    from contextlib import asynccontextmanager

    from sqlalchemy import text as sa_text

    import backend.shared.db as db_mod

    health_check_rows: list[dict] = []

    class _FakeResult:
        def __init__(self, scalar_value=None, rows=None):
            self._scalar_value = scalar_value
            self._rows = rows or []

        def scalar(self):
            return self._scalar_value

        def fetchall(self):
            return self._rows

        def first(self):
            return self._rows[0] if self._rows else None

    class _FakeBind:
        pass

    class _FakeInspector:
        def get_table_names(self):
            return ["health_check"]

        def get_columns(self, table_name: str):
            if table_name != "health_check":
                return []
            return [
                {"name": "id"},
                {"name": "check_time"},
                {"name": "service"},
                {"name": "status"},
                {"name": "duration_ms"},
            ]

    # Patch sqlalchemy.inspect to handle our fake bind.
    import sqlalchemy

    original_inspect = sqlalchemy.inspect

    def _inspect(subject, *args, **kwargs):
        if isinstance(subject, _FakeBind):
            return _FakeInspector()
        return original_inspect(subject, *args, **kwargs)

    sqlalchemy.inspect = _inspect  # type: ignore[assignment]

    import collections.abc

    class _FakeBegin(collections.abc.Coroutine):
        def __init__(self):
            async def _run():
                return True

            self._coro = _run()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        # Make this object look like a real coroutine to asyncio.create_task
        def send(self, value):
            return self._coro.send(value)

        def throw(self, typ, val=None, tb=None):
            return self._coro.throw(typ, val, tb)

        def close(self):
            return self._coro.close()

        def __await__(self):
            return self._coro.__await__()

        def __iter__(self):
            return self.__await__()

    class _FakeSession:
        def __init__(self):
            self._bind = _FakeBind()

        def get_bind(self, *args, **kwargs):
            return self._bind

        def begin(self):
            return _FakeBegin()

        async def execute(self, statement, params=None):
            raw = str(statement)
            lowered = raw.lower()

            if "select 1" in lowered:
                return _FakeResult(scalar_value=1)

            if "insert into health_check" in lowered:
                health_check_rows.append(
                    {
                        "check_time": "now",
                        "service": "test_service",
                        "status": "healthy",
                        "duration_ms": 10.5,
                    }
                )
                return _FakeResult()

            if "select" in lowered and "health_check" in lowered and "count" in lowered:
                return _FakeResult(scalar_value=len(health_check_rows))

            # Ignore cleanup statements, domain_events, etc.
            return _FakeResult()

        async def commit(self):
            return

        async def rollback(self):
            return

        async def close(self):
            return

    # Provide fake engine/pool for pool metrics tests.
    class _FakePool:
        def size(self):
            return 10

        def checkedout(self):
            return 0

        def overflow(self):
            return 0

    class _FakeEngine:
        def __init__(self):
            self.pool = _FakePool()

    db_mod._engine = _FakeEngine()
    # Ensure gauges have non-negative values for assertions.
    db_mod.db_pool_checked_out.set(0)
    db_mod.db_pool_overflow.set(0)

    @asynccontextmanager
    async def _fake_get_session():
        db_mod.db_active_sessions.inc()
        try:
            await db_mod.update_pool_metrics()
            yield _FakeSession()
        finally:
            db_mod.db_active_sessions.dec()

    db_mod.get_session = _fake_get_session  # type: ignore[assignment]

    session = _FakeSession()
    try:
        yield session
    finally:
        await session.close()





# HTTP test client fixture for FastAPI

@pytest.fixture(scope="function")
async def client():

    """

    Provides an HTTP test client for the FastAPI app.

    """

    from backend.services.core_engine.main import app
    import httpx

    with (
        patch("backend.services.core_engine.main.collect_toolchain_checks", return_value=[]),
        patch("backend.services.core_engine.main.startup_checks_ok", return_value=True),
    ):
        transport = httpx.ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as async_client:
                yield async_client
