"""Initial schema — programs and scans tables (proof of life for M1)

Revision ID: 001
Revises:
Create Date: 2026-03-06

Full schema is layered across milestones:
  001 — M1: programs, scans (skeleton)
  002 — M2: Full programs, program_scopes, program_policies
  003 — M3: scans, scan_stages, assets, endpoints
  004 — M3: js_assets, browser_sessions, api_schemas
  005 — M3: findings, finding_evidence, vulnerability_groups
  006 — M8: exploit_chains
  007 — M4: reports, reproduction_packs
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "programs",
        sa.Column(
            "program_id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("platform", sa.VARCHAR(50), nullable=False),
        sa.Column("handle", sa.VARCHAR(255), unique=True, nullable=False),
        sa.Column("name", sa.VARCHAR(500)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "queued_for_scan",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("last_scraped_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "scans",
        sa.Column(
            "scan_id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "program_id",
            sa.UUID(),
            sa.ForeignKey("programs.program_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.VARCHAR(50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Index for fast scan lookups by program
    op.create_index("ix_scans_program_id", "scans", ["program_id"])
    op.create_index("ix_scans_status", "scans", ["status"])


def downgrade() -> None:
    op.drop_index("ix_scans_status", table_name="scans")
    op.drop_index("ix_scans_program_id", table_name="scans")
    op.drop_table("scans")
    op.drop_table("programs")