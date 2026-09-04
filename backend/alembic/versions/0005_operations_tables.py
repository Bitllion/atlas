"""Create Phase 4a operations tables.

Revision ID: 0005_operations_tables
Revises: 0004_asset_tables
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_operations_tables"
down_revision: Union[str, None] = "0004_asset_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "fault_records",
        sa.Column("id", UUID, primary_key=True), sa.Column("object_id", UUID, nullable=False),
        sa.Column("fault_type", sa.String(100), nullable=False), sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("symptoms", sa.Text()), sa.Column("evidence", JSONB),
        sa.Column("source", sa.String(100), nullable=False), sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("reported_by", UUID), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"]), sa.ForeignKeyConstraint(["reported_by"], ["users.id"]),
        sa.CheckConstraint("fault_type IN ('HARDWARE','SOFTWARE','NETWORK','COOLING','POWER')", name="ck_fault_records_type"),
        sa.CheckConstraint("severity IN ('CRITICAL','HIGH','MEDIUM','LOW')", name="ck_fault_records_severity"),
    )
    op.create_index("idx_fault_records_object", "fault_records", ["object_id", sa.text("detected_at DESC")])
    op.create_index("idx_fault_records_severity", "fault_records", ["severity", sa.text("detected_at DESC")])

    op.create_table(
        "work_orders",
        sa.Column("id", UUID, primary_key=True), sa.Column("work_order_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("type", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False), sa.Column("status", sa.String(50), nullable=False, server_default="CREATED"),
        sa.Column("related_object_id", UUID), sa.Column("description", sa.Text()), sa.Column("fault_record_id", UUID),
        sa.Column("assigned_to", UUID), sa.Column("created_by", UUID, nullable=False), sa.Column("resolved_by", UUID),
        sa.Column("closed_by", UUID), sa.Column("assigned_at", sa.DateTime()), sa.Column("resolved_at", sa.DateTime()),
        sa.Column("closed_at", sa.DateTime()), sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime()), sa.Column("deleted_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["related_object_id"], ["objects.id"]), sa.ForeignKeyConstraint(["fault_record_id"], ["fault_records.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]), sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]), sa.ForeignKeyConstraint(["closed_by"], ["users.id"]),
        sa.CheckConstraint("type IN ('FAULT','REPAIR','INSPECTION','CHANGE')", name="ck_work_orders_type"),
        sa.CheckConstraint("priority IN ('CRITICAL','HIGH','MEDIUM','LOW')", name="ck_work_orders_priority"),
        sa.CheckConstraint("status IN ('CREATED','ASSIGNED','PROCESSING','WAITING','SUSPENDED','RESOLVED','CLOSED','CANCELLED','REOPENED')", name="ck_work_orders_status"),
    )
    op.create_index("idx_work_orders_assigned", "work_orders", ["assigned_to", "status"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_work_orders_object", "work_orders", ["related_object_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_work_orders_status", "work_orders", ["status", "priority", sa.text("created_at DESC")], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "repair_records",
        sa.Column("id", UUID, primary_key=True), sa.Column("work_order_id", UUID, nullable=False), sa.Column("object_id", UUID, nullable=False),
        sa.Column("repair_type", sa.String(100), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parts_used", JSONB), sa.Column("repair_result", sa.String(50), nullable=False),
        sa.Column("engineer_id", UUID, nullable=False), sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()), sa.Column("verification_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]), sa.ForeignKeyConstraint(["object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["engineer_id"], ["users.id"]),
        sa.CheckConstraint("repair_type IN ('REPLACEMENT','UPGRADE','ADJUSTMENT','CLEANING')", name="ck_repair_records_type"),
        sa.CheckConstraint("repair_result IN ('SUCCESS','FAILED','PARTIAL')", name="ck_repair_records_result"),
    )
    op.create_index("idx_repair_records_workorder", "repair_records", ["work_order_id"])
    op.create_index("idx_repair_records_object", "repair_records", ["object_id", sa.text("completed_at DESC")])

    op.create_table(
        "replacement_events",
        sa.Column("id", UUID, primary_key=True), sa.Column("repair_record_id", UUID),
        sa.Column("old_object_id", UUID, nullable=False), sa.Column("new_object_id", UUID, nullable=False),
        sa.Column("replacement_reason", sa.String(255), nullable=False), sa.Column("old_object_disposition", sa.String(100), nullable=False),
        sa.Column("engineer_id", UUID, nullable=False), sa.Column("replaced_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["repair_record_id"], ["repair_records.id"]), sa.ForeignKeyConstraint(["old_object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["new_object_id"], ["objects.id"]), sa.ForeignKeyConstraint(["engineer_id"], ["users.id"]),
        sa.CheckConstraint("replacement_reason IN ('FAILURE','UPGRADE','PREVENTIVE')", name="ck_replacement_events_reason"),
        sa.CheckConstraint("old_object_disposition IN ('RETIRED','RMA','STOCK','SCRAPPED')", name="ck_replacement_events_disposition"),
    )
    op.create_index("idx_replacement_events_old", "replacement_events", ["old_object_id", sa.text("replaced_at DESC")])
    op.create_index("idx_replacement_events_new", "replacement_events", ["new_object_id"])


def downgrade() -> None:
    op.drop_table("replacement_events")
    op.drop_table("repair_records")
    op.drop_table("work_orders")
    op.drop_table("fault_records")
