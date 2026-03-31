"""
Reporter schema: reports, reproduction_packs

Revision ID: 004
Revises: 003
Create Date: 2026-03-29
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003"
branch_labels = None

def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("report_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            sa.ForeignKey("programs.program_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("format", sa.VARCHAR(), nullable=False),  # pdf | docx
        sa.Column("status", sa.VARCHAR(), nullable=False),  # generating | completed | partial | failed
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("file_size_bytes", sa.INTEGER(), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_reports_scan_id", "reports", ["scan_id"])
    op.create_index("ix_reports_program_id", "reports", ["program_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_format", "reports", ["format"])
    op.create_unique_constraint("uq_reports_scan_format", "reports", ["scan_id", "format"])

    op.create_table(
        "reproduction_packs",
        sa.Column("pack_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "finding_id",
            UUID(as_uuid=True),
            sa.ForeignKey("findings.finding_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "report_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reports.report_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("curl_command", sa.TEXT(), nullable=True),
        sa.Column("http_request_raw", sa.TEXT(), nullable=True),
        sa.Column("browser_steps", sa.TEXT(), nullable=True),
        sa.Column("notes", sa.TEXT(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_reproduction_packs_report_id", "reproduction_packs", ["report_id"])
    op.create_index("ix_reproduction_packs_finding_id", "reproduction_packs", ["finding_id"])
    op.create_unique_constraint(
        "uq_reproduction_packs_report_finding",
        "reproduction_packs",
        ["report_id", "finding_id"],
    )


def downgrade() -> None:
    # Forward-only migration strategy for current development phase.
    pass
