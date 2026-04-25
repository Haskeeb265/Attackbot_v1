"""ensure timezone-aware timestamps

Revision ID: 005
Revises: 004
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure all timestamp columns are timezone-aware
    # PostgreSQL: TIMESTAMP WITH TIME ZONE

    # Convert scans.started_at to timestamptz
    op.execute("""
        ALTER TABLE scans 
        ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE 
        USING started_at AT TIME ZONE 'UTC'
    """)

    # Convert scans.completed_at to timestamptz
    op.execute("""
        ALTER TABLE scans 
        ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE 
        USING completed_at AT TIME ZONE 'UTC'
    """)

    # Convert scan_stages timestamps
    op.execute("""
        ALTER TABLE scan_stages 
        ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE 
        USING started_at AT TIME ZONE 'UTC'
    """)

    op.execute("""
        ALTER TABLE scan_stages 
        ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE 
        USING completed_at AT TIME ZONE 'UTC'
    """)

    # Convert reports timestamps
    op.execute("""
        ALTER TABLE reports 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
        USING created_at AT TIME ZONE 'UTC'
    """)

    op.execute("""
        ALTER TABLE reports 
        ALTER COLUMN generated_at TYPE TIMESTAMP WITH TIME ZONE 
        USING generated_at AT TIME ZONE 'UTC'
    """)


def downgrade():
    # Revert to timestamp without timezone
    op.execute("ALTER TABLE scans ALTER COLUMN started_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE scans ALTER COLUMN completed_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE scan_stages ALTER COLUMN started_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE scan_stages ALTER COLUMN completed_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE reports ALTER COLUMN created_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE reports ALTER COLUMN generated_at TYPE TIMESTAMP")
