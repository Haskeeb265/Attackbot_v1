import os
import sys
sys.path.insert(0, '.')

import asyncio
import asyncpg

# First, create the alembic_version table and mark migrations as done
async def setup_database():
    conn = await asyncpg.connect(
        user='attackbot',
        password='attackbot',
        host='localhost',
        port=5432,
        database='attackbot'
    )
    
    # Create alembic_version table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) PRIMARY KEY
        )
    """)
    
    # Mark all migrations as applied
    migrations = ['001', '002', '003', '004', '005', '006']
    for m in migrations:
        await conn.execute("INSERT INTO alembic_version (version_num) VALUES ($1) ON CONFLICT DO NOTHING", m)
    
    # Create all the tables needed
    await conn.execute("""
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
    """)
    
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_program_id ON scans(program_id)")
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key VARCHAR(36) PRIMARY KEY,
            service VARCHAR(50) NOT NULL,
            operation VARCHAR(100) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '7 days',
            response JSONB,
            entity_id UUID
        )
    """)
    
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_created_at ON idempotency_keys(created_at)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_expires_at ON idempotency_keys(expires_at)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_service_operation ON idempotency_keys(service, operation)")
    
    await conn.commit()
    await conn.close()

asyncio.run(setup_database())
print('Database setup complete')
