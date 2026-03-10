"""
AttackBot shared base configuration.
All services subclass BaseServiceConfig.
Values are loaded from environment variables via Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class BaseServiceConfig(BaseSettings):
    service_name: str = "attackbot-service"

    # ── Database ───────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://attackbot:attackbot@postgres:5432/attackbot"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # ── Redis ──────────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── RabbitMQ ───────────────────────────────────────────────────
    rabbitmq_url: str = "amqp://attackbot:attackbot@rabbitmq:5672/"

    # ── Vault ──────────────────────────────────────────────────────
    vault_url: str = "http://vault:8200"
    vault_token: str = "dev-root-token"

    # ── MinIO ──────────────────────────────────────────────────────
    minio_url: str = "http://minio:9000"
    minio_access_key: str = "attackbot"
    minio_secret_key: str = "attackbot123"
    minio_bucket_reports: str = "reports"
    minio_bucket_evidence: str = "evidence"
    minio_bucket_js_assets: str = "js-assets"
    minio_bucket_summaries: str = "summaries"

    # ── Logging ────────────────────────────────────────────────────
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
