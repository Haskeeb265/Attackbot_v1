"""
Add domain_events table for event sourcing.

Revision ID: 008
Revises: 007
Create Date: 2026-04-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create domain_events table
    op.create_table(
        "domain_events",
        sa.Column("event_id", UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("aggregate_type", sa.String(50), nullable=False),
        sa.Column("aggregate_id", UUID(as_uuid=True), nullable=False),
    )

    # Create indexes
    op.create_index("idx_domain_events_entity", "domain_events", ["entity_type", "entity_id"])
    op.create_index("idx_domain_events_aggregate", "domain_events", ["aggregate_type", "aggregate_id"])
    op.create_index("idx_domain_events_sequence", "domain_events", ["sequence"])
    op.create_index("idx_domain_events_timestamp", "domain_events", ["timestamp"])
    op.create_index("idx_domain_events_event_type", "domain_events", ["event_type"])

    # Create sequence for sequence numbers
    op.execute("CREATE SEQUENCE domain_event_sequence_seq INCREMENT BY 1 START 1")


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_domain_events_entity", table_name="domain_events")
    op.drop_index("idx_domain_events_aggregate", table_name="domain_events")
    op.drop_index("idx_domain_events_sequence", table_name="domain_events")
    op.drop_index("idx_domain_events_timestamp", table_name="domain_events")
    op.drop_index("idx_domain_events_event_type", table_name="domain_events")

    # Drop table
    op.drop_table("domain_events")

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS domain_event_sequence_seq")
