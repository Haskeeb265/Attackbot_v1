"""
Full scraper schema — programs, program_scopes, program_policies

Revision ID: 002
Revises: 001
Create Date: 2026-03-10

Tables created: programs (full), program_scopes, program_policies
Tables modified: scans (FK recreated)
"""
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


def upgrade() -> None:
    # ── Drop skeleton tables from 001 (scans depends on programs) ──
    op.drop_table("scans")
    op.drop_table("programs")

    # ── programs — full schema ─────────────────────────────────────
    op.create_table(
        "programs",
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("platform",        sa.VARCHAR(50),   nullable=False),
        sa.Column("handle",          sa.VARCHAR(255),  nullable=False, unique=True),
        sa.Column("name",            sa.VARCHAR(500)),
        sa.Column("url",             sa.VARCHAR(2048)),
        sa.Column("bounty_type",     sa.VARCHAR(50)),   # 'paid' | 'rep_only' | 'swag'
        sa.Column("max_bounty",      sa.INTEGER),
        sa.Column("is_active",       sa.Boolean(),    server_default="true"),
        sa.Column("summary_file",    sa.VARCHAR(1024)),
        sa.Column("raw_policy",      JSONB),
        sa.Column("queued_for_scan", sa.Boolean(),    server_default="false"),
        sa.Column("last_scraped_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at",      sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at",      sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_programs_platform",        "programs", ["platform"])
    op.create_index("ix_programs_queued_for_scan", "programs", ["queued_for_scan"])
    op.create_index("ix_programs_is_active",       "programs", ["is_active"])

    # ── program_scopes ─────────────────────────────────────────────
    op.create_table(
        "program_scopes",
        sa.Column(
            "scope_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            sa.ForeignKey("programs.program_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope_type", sa.VARCHAR(20),   nullable=False),  # in_scope | out_of_scope
        sa.Column("asset_type", sa.VARCHAR(50),   nullable=False),  # url | domain | wildcard_domain | ip_range | mobile_app | api
        sa.Column("value",      sa.VARCHAR(2048), nullable=False),
        sa.Column("notes",      sa.TEXT()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_program_scopes_program_id", "program_scopes", ["program_id"])
    op.create_index("ix_program_scopes_scope_type", "program_scopes", ["scope_type"])

    # ── program_policies ──────────────────────────────────────────
    op.create_table(
        "program_policies",
        sa.Column(
            "policy_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            sa.ForeignKey("programs.program_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("disclosure_policy",    sa.TEXT()),
        sa.Column("testing_restrictions", ARRAY(sa.TEXT())),
        sa.Column("safe_harbor",          sa.Boolean()),
        sa.Column("created_at",           sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── Restore scans pointing to new programs ─────────────────────
    op.create_table(
        "scans",
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            sa.ForeignKey("programs.program_id"),
            nullable=False,
        ),
        sa.Column("status",      sa.VARCHAR(50), server_default="pending"),
        sa.Column("retry_count", sa.INTEGER(),   server_default="0"),
        sa.Column("created_at",  sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_scans_program_id", "scans", ["program_id"])
    op.create_index("ix_scans_status",     "scans", ["status"])


def downgrade() -> None:
    op.drop_table("scans")
    op.drop_table("program_policies")
    op.drop_table("program_scopes")
    op.drop_table("programs")

    # Restore minimal skeleton from 001
    op.create_table(
        "programs",
        sa.Column("program_id",      UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("platform",        sa.VARCHAR(50),  nullable=False),
        sa.Column("handle",          sa.VARCHAR(255), unique=True, nullable=False),
        sa.Column("name",            sa.VARCHAR(500)),
        sa.Column("is_active",       sa.Boolean(),    server_default="true"),
        sa.Column("queued_for_scan", sa.Boolean(),    server_default="false"),
        sa.Column("last_scraped_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at",      sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at",      sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_table(
        "scans",
        sa.Column("scan_id",    UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("program_id", UUID(as_uuid=True),
                  sa.ForeignKey("programs.program_id"), nullable=False),
        sa.Column("status",     sa.VARCHAR(50), server_default="pending"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )