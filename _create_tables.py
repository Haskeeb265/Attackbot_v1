import os
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot'

import sys
sys.path.insert(0, '.')

from backend.shared.db import init_db, get_engine
from backend.shared.models.scans import Scan
from backend.shared.models.idempotency import IdempotencyKey
from sqlalchemy import text

init_db('postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot')

# Get the engine and create all tables
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

async def create_tables():
    engine = get_engine()
    async with engine.begin() as conn:
        # Check existing tables
        rows = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        existing = [r[0] for r in rows.fetchall()]
        print(f"Existing tables: {existing}")
        
        # Create alembic_version table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) PRIMARY KEY
            )
        """))
        
        # Mark migrations as applied
        # Insert all migrations up to 006
        migrations = ['001', '002', '003', '004', '005', '006']
        for m in migrations:
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v) ON CONFLICT DO NOTHING"), {'v': m})
        
        # Now create Scan table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id UUID PRIMARY KEY,
                program_id UUID NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'running',
                priority INTEGER NOT NULL DEFAULT 1,
                feature_flags JSONB,
                retry_count INTEGER NOT NULL DEFAULT 0,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                error_detail TEXT,
                finding_count INTEGER DEFAULT 0,
                severity_breakdown JSONB DEFAULT '{}',
                partial_detail JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        
        # Create indexes for scans
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scans_program_id ON scans(program_id)"))
        
        # Create idempotency_keys table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                key VARCHAR(36) PRIMARY KEY,
                service VARCHAR(50) NOT NULL,
                operation VARCHAR(100) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '7 days',
                response JSONB,
                entity_id UUID
            )
        """))
        
        # Create indexes for idempotency_keys
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_idempotency_createdAt ON idempotency_keys(created_at)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_idempotency_expiresAt ON idempotency_keys(expires_at)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_idempotency_service_operation ON idempotency_keys(service, operation)"))
        
        await conn.commit()
    
    # Verify
    async with engine.begin() as conn:
        rows = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        final = [r[0] for r in rows.fetchall()]
        print(f"Final tables: {final}")

asyncio.run(create_tables())
