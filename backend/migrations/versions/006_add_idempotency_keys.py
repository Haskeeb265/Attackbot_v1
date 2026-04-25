"""add idempotency keys table

Revision ID: 006
Revises: 005
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(36), primary_key=True),
        sa.Column('service', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response', postgresql.JSONB, nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index(
        'idx_idempotency_created_at',
        'idempotency_keys',
        ['created_at']
    )

    op.create_index(
        'idx_idempotency_expires_at',
        'idempotency_keys',
        ['expires_at']
    )

    op.create_index(
        'idx_idempotency_service_operation',
        'idempotency_keys',
        ['service', 'operation']
    )


def downgrade():
    op.drop_table('idempotency_keys')
