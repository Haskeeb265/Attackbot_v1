# backend/migrations/env.py
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Alembic Config object — provides access to values within alembic.ini
config = context.config

# Set up Python logging from the alembic.ini config section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load DATABASE_URL from environment — never hardcode credentials
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "The migrate container requires this to run Alembic."
    )

config.set_main_option("sqlalchemy.url", database_url)

# Import all models here so Alembic can detect changes for autogenerate.
# Add imports for each new model as milestones are implemented.
# from backend.services.scraper.models import *  # noqa: F401, F403 (uncomment in M2)

target_metadata = None  # updated to Base.metadata once models are imported


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations with a live async DB connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())