"""
Full scraper schema: programs (extended), program_scopes, program_policies

Revision ID: 002
Revises: 001
Create Date: 2026-03-10

Tables modified: programs (add columns)
Tables created: program_scopes, program_policies

Strategy: extend forward — never drop columns from 001.
queued_for_scan EXCLUDED from ON CONFLICT update — reconciler owns it.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def upgrade() -> None:
    # --- Extend programs table ---
    # 001 created programs with only program_id, platform, handle, name, created_at
    # We add all remaining canonical columns here.
    # Guard each with _column_exists to be safe if 001 had extras.

    if not _column_exists("programs", "url"):
        op.add_column("programs", sa.Column("url", sa.VARCHAR(), nullable=True))
    if not _column_exists("programs", "bounty_type"):
        op.add_column("programs", sa.Column("bounty_type", sa.VARCHAR(), nullable=True))
    if not _column_exists("programs", "max_bounty"):
        op.add_column("programs", sa.Column("max_bounty", sa.INTEGER(), nullable=True))
    if not _column_exists("programs", "is_active"):
        op.add_column("programs", sa.Column(
            "is_active", sa.BOOLEAN(), nullable=False, server_default="true"
        ))
    if not _column_exists("programs", "summary_file"):
        op.add_column("programs", sa.Column("summary_file", sa.VARCHAR(), nullable=True))
    if not _column_exists("programs", "raw_policy"):
        op.add_column("programs", sa.Column("raw_policy", JSONB(), nullable=True))
    if not _column_exists("programs", "queued_for_scan"):
        op.add_column("programs", sa.Column(
            "queued_for_scan", sa.BOOLEAN(), nullable=False, server_default="false"
        ))
    if not _column_exists("programs", "last_scraped_at"):
        op.add_column("programs", sa.Column("last_scraped_at", sa.TIMESTAMP(timezone=True), nullable=True))

    if not _column_exists("programs", "updated_at"):
        op.add_column("programs", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True))

    # Indexes for reconciler and filtering queries
    bind = op.get_bind()

    def index_exists(name: str) -> bool:
        r = bind.execute(sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname = :n"
        ), {"n": name})
        return r.fetchone() is not None

    if not index_exists("ix_programs_queued"):
        op.create_index("ix_programs_queued", "programs", ["queued_for_scan"])
    if not index_exists("ix_programs_platform"):
        op.create_index("ix_programs_platform", "programs", ["platform"])
    if not index_exists("ix_programs_handle"):
        op.create_index("ix_programs_handle", "programs", ["handle"])

    # --- Create program_scopes ---
    op.create_table(
        "program_scopes",
        sa.Column(
            "scope_id", UUID(as_uuid=True), primary_key=True,
            default=uuid.uuid4
        ),
        sa.Column(
            "program_id", UUID(as_uuid=True),
            sa.ForeignKey("programs.program_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope_type", sa.VARCHAR(), nullable=False),    # in_scope | out_of_scope
        sa.Column("asset_type", sa.VARCHAR(), nullable=False),    # url | domain | wildcard_domain | ip_range | mobile_app | api
        sa.Column("value", sa.VARCHAR(), nullable=False),
        sa.Column("notes", sa.TEXT(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False,
            server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_program_scopes_program_id", "program_scopes", ["program_id"])
    op.create_index("ix_program_scopes_scope_type", "program_scopes", ["scope_type"])

    # --- Create program_policies ---
    op.create_table(
        "program_policies",
        sa.Column(
            "policy_id", UUID(as_uuid=True), primary_key=True,
            default=uuid.uuid4
        ),
        sa.Column(
            "program_id", UUID(as_uuid=True),
            sa.ForeignKey("programs.program_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("disclosure_policy", sa.TEXT(), nullable=True),
        sa.Column("testing_restrictions", sa.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("safe_harbor", sa.BOOLEAN(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False,
            server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_program_policies_program_id", "program_policies", ["program_id"])

    # Required for ON CONFLICT (program_id) in repository._upsert_policy()
    op.create_unique_constraint(
        "uq_program_policies_program_id", "program_policies", ["program_id"]
    )


def downgrade() -> None:
    pass  # forward-only in development