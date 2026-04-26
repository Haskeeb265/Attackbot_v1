from alembic import op
import sqlalchemy as sa

revision = "008_add_health_check_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "health_check",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("check_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
    )
    op.create_index("idx_health_check_time", "health_check", ["check_time"])


def downgrade():
    op.drop_index("idx_health_check_time", table_name="health_check")
    op.drop_table("health_check")

