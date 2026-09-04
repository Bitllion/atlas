"""Create the generic workflow engine tables.

Revision ID: 0007_workflow_tables
Revises: 0006_knowledge_tables
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0007_workflow_tables"
down_revision: Union[str, None] = "0006_knowledge_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "workflow_definition",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("definition", JSONB, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime()),
        sa.Column("deleted_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", UUID),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.UniqueConstraint("name", name="uq_workflow_definition_name"),
        sa.UniqueConstraint("code", name="uq_workflow_definition_code"),
        sa.CheckConstraint("version > 0", name="ck_workflow_definition_version"),
    )
    op.create_index("idx_workflow_definition_active", "workflow_definition", ["is_active"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "workflow_instance",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("definition_id", UUID, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID, nullable=False),
        sa.Column("business_key", sa.String(255)),
        sa.Column("current_node_id", sa.String(100)),
        sa.Column("status", sa.String(50), nullable=False, server_default="RUNNING"),
        sa.Column("started_by", UUID, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("deleted_at", sa.DateTime()),
        sa.Column("deleted_by", UUID),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["definition_id"], ["workflow_definition.id"]),
        sa.ForeignKeyConstraint(["started_by"], ["users.id"]),
        sa.CheckConstraint("status IN ('RUNNING','COMPLETED','TERMINATED')", name="ck_workflow_instance_status"),
        sa.CheckConstraint("version > 0", name="ck_workflow_instance_version"),
    )
    op.create_index("idx_workflow_instance_entity", "workflow_instance", ["entity_type", "entity_id"])
    op.create_index("idx_workflow_instance_status", "workflow_instance", ["status", sa.text("started_at DESC")], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "workflow_task",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("instance_id", UUID, nullable=False),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("assignee_id", UUID, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("comment", sa.Text()),
        sa.Column("actioned_by", UUID),
        sa.Column("actioned_at", sa.DateTime()),
        sa.Column("deleted_at", sa.DateTime()),
        sa.Column("deleted_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["instance_id"], ["workflow_instance.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["actioned_by"], ["users.id"]),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED','SKIPPED')", name="ck_workflow_task_status"),
    )
    op.create_index("idx_workflow_task_instance", "workflow_task", ["instance_id", "created_at"])
    op.create_index("idx_workflow_task_assignee", "workflow_task", ["assignee_id", "status"], postgresql_where=sa.text("status = 'PENDING' AND deleted_at IS NULL"))

    op.create_foreign_key(
        "fk_purchase_requests_workflow_instance",
        "purchase_requests", "workflow_instance",
        ["workflow_instance_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_purchase_requests_workflow_instance", "purchase_requests", type_="foreignkey")
    op.drop_table("workflow_task")
    op.drop_table("workflow_instance")
    op.drop_table("workflow_definition")
