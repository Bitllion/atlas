"""Create import job and error tables.

Revision ID: 0003_import_tables
Revises: 0002_core_tables
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_import_tables"
down_revision: Union[str, None] = "0002_core_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("preview_data", JSONB, nullable=True),
        sa.Column("error_summary", JSONB, nullable=True),
        sa.Column("created_by", UUID, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", UUID, nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint("format IN ('XLSX', 'CSV')", name="ck_import_jobs_format"),
        sa.CheckConstraint(
            "status IN ('PREVIEWING', 'PREVIEWED', 'EXECUTING', 'SUCCEEDED', "
            "'PARTIAL_FAILED', 'FAILED')",
            name="ck_import_jobs_status",
        ),
    )
    op.create_index("idx_import_jobs_status_created", "import_jobs", ["status", "created_at"])
    op.create_index("idx_import_jobs_created_by", "import_jobs", ["created_by"])
    op.create_index("idx_import_jobs_active", "import_jobs", ["id"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "import_errors",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("import_job_id", UUID, nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(255), nullable=True),
        sa.Column("error_type", sa.String(100), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("raw_data", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_import_errors_job_row", "import_errors", ["import_job_id", "row_number"])


def downgrade() -> None:
    op.drop_table("import_errors")
    op.drop_table("import_jobs")
