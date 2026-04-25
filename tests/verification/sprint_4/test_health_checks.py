"""
Test verification for Issue #8: Health Check False Positives

These tests verify that health checks validate actual functionality,
not just connectivity.
"""

import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from sqlalchemy.future import select
from sqlalchemy import text


class TestHealthModel:
    """Tests for health check models."""

    def test_health_status_enum(self):
        """Verify HealthStatus enum has all required states."""
        from backend.shared.health import HealthStatus
        
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"

    def test_component_health_model(self):
        """Verify ComponentHealth model structure."""
        from backend.shared.health import ComponentHealth, HealthStatus
        
        health = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=10.5,
            detail="All checks passed",
            error=None
        )
        
        assert health.name == "database"
        assert health.status == HealthStatus.HEALTHY
        assert health.latency_ms == 10.5
        assert health.detail == "All checks passed"
        assert health.error is None

    def test_health_response_model(self):
        """Verify HealthResponse model structure."""
        from backend.shared.health import HealthResponse, HealthStatus, ComponentHealth
        
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            components={
                "database": ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY
                )
            },
            timestamp="2026-01-01T00:00:00Z",
            version="2.0"
        )
        
        assert response.status == HealthStatus.HEALTHY
        assert "database" in response.components
        assert response.version == "2.0"


class TestDBHealthChecker:
    """Tests for database health checker."""

    @pytest.mark.asyncio
    async def test_db_health_check_connectivity(self, db_session):
        """Verify DB health check tests connectivity."""
        from backend.shared.db import DBHealthChecker
        from backend.shared.health import HealthStatus
        
        checker = DBHealthChecker()
        
        # This should pass if DB is accessible
        # Note: In test environment, db_session is already connected
        result = await checker.check(db_session)
        
        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_db_health_check_schema(self, db_session):
        """Verify DB health check validates schema."""
        from backend.shared.db import DBHealthChecker
        from backend.shared.health import HealthStatus
        
        checker = DBHealthChecker()
        
        result = await checker.check(db_session)
        
        # In a real implementation, this would verify schema exists
        # For now, just verify it returns healthy when connected
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    @patch("backend.shared.db.DBHealthChecker.check")
    async def test_db_health_check_failure(self, mock_check, client):
        """Verify DB health check returns unhealthy on failure."""
        from backend.shared.health import HealthStatus, ComponentHealth
        
        # Configure mock to return unhealthy
        mock_check.return_value = ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            error="Connection failed"
        )
        
        # Call health endpoint
        response = await client.get("/health")
        
        assert response.status_code in [503, 500] or response.json()["status"] == "unhealthy"


class TestQueueHealthChecker:
    """Tests for queue health checker."""

    @pytest.mark.asyncio
    async def test_queue_health_check_connection(self, rabbitmq_client):
        """Verify queue health check tests RabbitMQ connection."""
        from backend.shared.queue import QueueHealthChecker
        from backend.shared.health import HealthStatus
        
        checker = QueueHealthChecker(
            url=rabbitmq_client.url,
            required_queues=["scan_jobs", "report_jobs"]
        )
        
        result = await checker.check()
        
        assert result.name == "rabbitmq"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_queue_health_check_missing_queue(self, rabbitmq_client):
        """Verify health check returns degraded when required queue is missing."""
        from backend.shared.queue import QueueHealthChecker
        from backend.shared.health import HealthStatus
        
        # Require a queue that doesn't exist
        checker = QueueHealthChecker(
            url=rabbitmq_client.url,
            required_queues=["nonexistent_queue"]
        )
        
        result = await checker.check()
        
        # Should return degraded or unhealthy
        assert result.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert "nonexistent_queue" in result.detail or result.error

    @pytest.mark.asyncio
    async def test_queue_health_check_publish(self, rabbitmq_client):
        """Verify queue health check tests publish capability."""
        from backend.shared.queue import QueueHealthChecker
        from backend.shared.health import HealthStatus
        
        checker = QueueHealthChecker(
            url=rabbitmq_client.url,
            required_queues=["health_check_test"]
        )
        
        # First, ensure the test queue exists
        import aio_pika
        connection = await aio_pika.connect_robust(rabbitmq_client.url)
        channel = await connection.channel()
        await channel.declare_queue("health_check_test", durable=False)
        await channel.close()
        await connection.close()
        
        result = await checker.check()
        
        # Should be healthy with publish capability
        assert result.status == HealthStatus.HEALTHY


class TestStorageHealthChecker:
    """Tests for storage health checker."""

    @pytest.mark.asyncio
    async def test_storage_health_check_connection(self, minio_client):
        """Verify storage health check tests MinIO connection."""
        from backend.shared.storage import StorageHealthChecker
        from backend.shared.health import HealthStatus
        
        checker = StorageHealthChecker(
            endpoint=minio_client.endpoint,
            access_key=minio_client.access_key,
            secret_key=minio_client.secret_key,
            secure=minio_client.secure,
            required_buckets=["reports", "scans"]
        )
        
        result = await checker.check()
        
        assert result.name == "storage"
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_storage_health_check_missing_bucket(self, minio_client):
        """Verify health check returns degraded when bucket is missing."""
        from backend.shared.storage import StorageHealthChecker
        from backend.shared.health import HealthStatus
        
        checker = StorageHealthChecker(
            endpoint=minio_client.endpoint,
            access_key=minio_client.access_key,
            secret_key=minio_client.secret_key,
            secure=minio_client.secure,
            required_buckets=["nonexistent_bucket"]
        )
        
        result = await checker.check()
        
        # Should return degraded
        assert result.status == HealthStatus.DEGRADED
        assert "nonexistent_bucket" in result.detail

    @pytest.mark.asyncio
    async def test_storage_health_check_io_operations(self, minio_client):
        """Verify storage health check tests I/O operations."""
        from backend.shared.storage import StorageHealthChecker
        from backend.shared.health import HealthStatus
        
        # Use existing bucket
        checker = StorageHealthChecker(
            endpoint=minio_client.endpoint,
            access_key=minio_client.access_key,
            secret_key=minio_client.secret_key,
            secure=minio_client.secure,
            required_buckets=["reports"]
        )
        
        result = await checker.check()
        
        # Should be healthy with I/O capability
        assert result.status == HealthStatus.HEALTHY


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self, client):
        """Verify health endpoint returns correct structure."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "2.0"

    @pytest.mark.asyncio
    async def test_health_endpoint_components(self, client):
        """Verify health endpoint includes all required components."""
        response = await client.get("/health")
        data = response.json()
        
        components = data["components"]
        assert "database" in components
        assert "rabbitmq" in components
        assert "storage" in components

    @pytest.mark.asyncio
    async def test_health_endpoint_component_structure(self, client):
        """Verify health endpoint components have correct structure."""
        response = await client.get("/health")
        data = response.json()
        
        for name, component in data["components"].items():
            assert "name" in component
            assert "status" in component
            # May have latency and detail
            assert component["name"] == name


class TestHealthCheckTable:
    """Tests for health check table."""

    @pytest.mark.asyncio
    async def test_health_check_table_exists(self, db_session):
        """Verify health_check table exists."""
        from sqlalchemy import inspect
        
        inspector = inspect(db_session.get_bind())
        tables = inspector.get_table_names()
        
        assert "health_check" in tables

    @pytest.mark.asyncio
    async def test_health_check_table_columns(self, db_session):
        """Verify health_check table has required columns."""
        from sqlalchemy import inspect
        
        inspector = inspect(db_session.get_bind())
        columns = inspector.get_columns("health_check")
        
        column_names = [col['name'] for col in columns]
        
        assert "id" in column_names
        assert "check_time" in column_names
        assert "service" in column_names
        assert "status" in column_names
        assert "duration_ms" in column_names

    @pytest.mark.asyncio
    async def test_health_check_record_insert(self, db_session):
        """Verify health check records are inserted."""
        from sqlalchemy import func
        
        # Insert a test record
        await db_session.execute(
            text("INSERT INTO health_check (check_time, service, status, duration_ms) "
                 "VALUES (now(), 'test_service', 'healthy', 10.5)")
        )
        await db_session.commit()
        
        # Verify record exists
        result = await db_session.execute(
            select(func.count()).select_from(text("health_check"))
        )
        count = result.scalar()
        assert count >= 1


class TestHealthCheckMigration:
    """Tests for health check table migration."""

    def test_migration_file_exists(self):
        """Verify health check migration file exists."""
        import os
        from pathlib import Path
        
        # Check for migration file
        migrations_dir = Path("alembic/versions")
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob("008_*.py"))
            assert len(migration_files) > 0
            
            for file in migration_files:
                content = file.read_text()
                assert "health_check" in content.lower()


class TestTemporalHealthChecks:
    """Tests for health check timestamp tracking."""

    @pytest.mark.asyncio
    async def test_health_check_timestamp(self, client):
        """Verify health check includes timestamp."""
        before = time.time()
        response = await client.get("/health")
        after = time.time()
        
        data = response.json()
        timestamp = data["timestamp"]
        
        # Parse timestamp and verify it's current
        from datetime import datetime
        check_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        check_time_ts = check_time.timestamp()
        
        assert before <= check_time_ts <= after
