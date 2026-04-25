"""change idempotency keys primary key to composite

Revision ID: 007
Revises: 006
Create Date: 2026-04-25

"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing primary key constraint
    op.drop_constraint('idempotency_keys_pkey', 'idempotency_keys', type_='primary')
    
    # Create composite primary key
    op.create_primary_key('pk_idempotency', 'idempotency_keys', ['key', 'service', 'operation'])


def downgrade():
    # Drop the composite primary key
    op.drop_constraint('pk_idempotency', 'idempotency_keys', type_='primary')
    
    # Recreate single-column primary key
    op.create_primary_key('idempotency_keys_pkey', 'idempotency_keys', ['key'])
