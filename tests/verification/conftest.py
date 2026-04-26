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





# Database session fixture

@pytest.fixture(scope="function")
async def db_session():
    """
    Provides an async database session with automatic cleanup.
    """
    from backend.shared.db import init_db, get_session
    from sqlalchemy import text
    
    # Initialize DB with test URL
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot")
    init_db(db_url)
    
    async with get_session() as session:
        yield session
        # Clean up all test data by truncating tables
        # This ensures isolation between tests
        try:
            await session.execute(text("TRUNCATE TABLE domain_events CASCADE"))
            await session.execute(text("ALTER SEQUENCE domain_event_sequence_seq RESTART WITH 1"))
            await session.commit()
        except Exception:
            await session.rollback()
        await session.close()





# HTTP test client fixture for FastAPI

@pytest.fixture(scope="function")

def client():

    """

    Provides an HTTP test client for the FastAPI app.

    """

    from fastapi.testclient import TestClient

    from backend.services.core_engine.main import app
    with (
        patch("backend.services.core_engine.main.collect_toolchain_checks", return_value=[]),
        patch("backend.services.core_engine.main.startup_checks_ok", return_value=True),
    ):
        with TestClient(app, raise_server_exceptions=False) as client:

            yield client
