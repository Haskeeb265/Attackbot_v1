# backend/shared/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceConfig(BaseSettings):
    """
    Base configuration inherited by every service.
    Each service subclasses this and adds its own fields.
    Settings are loaded from environment variables (with optional .env fallback).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ───────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── RabbitMQ ───────────────────────────────────────────────────────
    rabbitmq_url: str = "amqp://attackbot:attackbot@localhost:5672/"

    # ── Vault ──────────────────────────────────────────────────────────
    vault_url: str = "http://localhost:8200"
    vault_token: str = "dev-root-token"

    # ── MinIO ──────────────────────────────────────────────────────────
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    # ── Service identity ───────────────────────────────────────────────
    service_name: str = "unknown"
    log_level: str = "INFO"
    environment: str = "development"
    jaeger_endpoint: str = "http://jaeger:14268/api/traces"

    # E2E timeout scaling
    e2e_tool_timeout_scale: float = 1.0
    e2e_tool_timeout_floor_seconds: int = 30

    def scaled_timeout(self, timeout_seconds: int) -> int:
        """
        Scale per-tool timeout for E2E runs while keeping production defaults readable.
        """
        base_timeout = max(int(timeout_seconds), 0)
        scale = float(self.e2e_tool_timeout_scale)
        if scale <= 0:
            scale = 1.0
        scaled = int(base_timeout * scale)
        floor = max(int(self.e2e_tool_timeout_floor_seconds), 1)
        return max(scaled, floor)

    def scaled_scan_timeout_seconds(self, timeout_seconds: int) -> int:
        """
        Scale scan-level timeout with schema-safe minimum.
        """
        return max(self.scaled_timeout(timeout_seconds), 300)

    def is_placeholder(self, field_name: str) -> bool:
        value = getattr(self, field_name)
        if value is None:
            return True
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized in {"", "placeholder", "changeme", "replace-me"}
        return False

    def require_fields(self, field_names: list[str]) -> None:
        missing = [field_name for field_name in field_names if self.is_placeholder(field_name)]
        if missing:
            raise RuntimeError(
                f"{self.service_name} missing required configuration: {', '.join(missing)}"
            )


class QueueConfig(BaseSettings):
    """Queue configuration with backpressure support (Sprint #4)."""

    rabbitmq_url: str = "amqp://localhost"
    max_queue_depths: dict[str, int] = {
        "scan_jobs": 1000,
        "report_jobs": 500,
        "dlq": 10000,
    }

    @property
    def default_max_depth(self) -> int:
        # Conservative default suitable for tests; can be overridden per queue.
        return 1000
