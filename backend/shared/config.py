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