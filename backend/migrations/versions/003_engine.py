"""
Full engine schema: scans (extended), scan_stages, assets, endpoints,
js_assets, findings, finding_evidence, vulnerability_groups

Revision ID: 003
Revises: 002
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ---- Extend scans table ----
    op.add_column("scans", sa.Column("priority", sa.INTEGER(), nullable=True))
    op.add_column("scans", sa.Column("feature_flags", JSONB(), nullable=True))
    op.add_column("scans", sa.Column("partial_detail", JSONB(), nullable=True))
    op.add_column("scans", sa.Column("error_detail", sa.TEXT(), nullable=True))
    op.add_column(
        "scans",
        sa.Column("finding_count", sa.INTEGER(), nullable=False, server_default="0"),
    )
    op.add_column("scans", sa.Column("severity_breakdown", JSONB(), nullable=True))
    op.add_column(
        "scans",
        sa.Column("retry_count", sa.INTEGER(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scans",
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "scans",
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_index("ix_scans_program_id", "scans", ["program_id"])
    op.create_index("ix_scans_status", "scans", ["status"])

    # ---- scan_stages ----
    op.create_table(
        "scan_stages",
        sa.Column("stage_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage_number", sa.FLOAT(), nullable=False),
        sa.Column("stage_name", sa.VARCHAR(), nullable=False),
        sa.Column("status", sa.VARCHAR(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
        sa.Column("output_summary", JSONB(), nullable=True),
    )

    op.create_index("ix_scan_stages_scan_id", "scan_stages", ["scan_id"])

    # ---- assets ----
    op.create_table(
        "assets",
        sa.Column("asset_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_type", sa.VARCHAR(), nullable=False),
        sa.Column("value", sa.VARCHAR(), nullable=False),
        sa.Column("is_in_scope", sa.BOOLEAN(), nullable=False, server_default="true"),
        sa.Column("technology_stack", JSONB(), nullable=True),
        sa.Column("waf_detected", sa.VARCHAR(), nullable=True),
        sa.Column("http_status", sa.INTEGER(), nullable=True),
        sa.Column(
            "discovered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_assets_scan_id", "assets", ["scan_id"])

    # ---- endpoints ----
    op.create_table(
        "endpoints",
        sa.Column("endpoint_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "asset_id",
            UUID(as_uuid=True),
            sa.ForeignKey("assets.asset_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("method", sa.VARCHAR(), nullable=False),
        sa.Column("path", sa.VARCHAR(), nullable=False),
        sa.Column("full_url", sa.VARCHAR(), nullable=False),
        sa.Column("content_type", sa.VARCHAR(), nullable=True),
        sa.Column("response_code", sa.INTEGER(), nullable=True),
        sa.Column("parameters", JSONB(), nullable=True),
        sa.Column("headers", JSONB(), nullable=True),
        sa.Column("requires_auth", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column(
            "discovered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_endpoints_scan_id", "endpoints", ["scan_id"])
    op.create_index("ix_endpoints_asset_id", "endpoints", ["asset_id"])

    # ---- js_assets ----
    op.create_table(
        "js_assets",
        sa.Column("js_asset_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.VARCHAR(), nullable=False),
        sa.Column("content_hash", sa.VARCHAR(), nullable=True),
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("size_bytes", sa.INTEGER(), nullable=True),
        sa.Column("analyzed", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column(
            "discovered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_js_assets_scan_id", "js_assets", ["scan_id"])
    op.create_unique_constraint(
        "uq_js_assets_content_hash", "js_assets", ["content_hash"]
    )

    # ---- findings ----
    op.create_table(
        "findings",
        sa.Column("finding_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("program_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.VARCHAR(), nullable=False),
        sa.Column("vulnerability_type", sa.VARCHAR(), nullable=False),
        sa.Column("severity", sa.VARCHAR(), nullable=False),
        sa.Column("cvss_score", sa.FLOAT(), nullable=True),
        sa.Column("cvss_vector", sa.VARCHAR(), nullable=True),
        sa.Column("affected_url", sa.VARCHAR(), nullable=False),
        sa.Column("affected_parameter", sa.VARCHAR(), nullable=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("reproduction_steps", sa.TEXT(), nullable=True),
        sa.Column("is_verified", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column("is_false_positive", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column("false_positive_reason", sa.TEXT(), nullable=True),
        sa.Column("deduplication_hash", sa.VARCHAR(), nullable=False),
        sa.Column("source", sa.VARCHAR(), nullable=True),
        sa.Column("raw_output", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_findings_scan_id", "findings", ["scan_id"])
    op.create_index("ix_findings_program_id", "findings", ["program_id"])

    op.create_unique_constraint(
        "uq_findings_dedup_hash_scan",
        "findings",
        ["deduplication_hash", "scan_id"],
    )

    # ---- finding_evidence ----
    op.create_table(
        "finding_evidence",
        sa.Column("evidence_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "finding_id",
            UUID(as_uuid=True),
            sa.ForeignKey("findings.finding_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("artifact_type", sa.VARCHAR(), nullable=False),
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column(
            "captured_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        "ix_finding_evidence_finding_id",
        "finding_evidence",
        ["finding_id"],
    )

    # ---- vulnerability_groups ----
    op.create_table(
        "vulnerability_groups",
        sa.Column("group_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.scan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vulnerability_type", sa.VARCHAR(), nullable=False),
        sa.Column("affected_count", sa.INTEGER(), nullable=False, server_default="0"),
        sa.Column("max_severity", sa.VARCHAR(), nullable=True),
        sa.Column("finding_ids", ARRAY(UUID(as_uuid=True)), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        "ix_vulnerability_groups_scan_id",
        "vulnerability_groups",
        ["scan_id"],
    )


def downgrade() -> None:
    pass