"""Create Phase 3a asset lifecycle tables.

Revision ID: 0004_asset_tables
Revises: 0003_import_tables
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_asset_tables"
down_revision: Union[str, None] = "0003_import_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "purchase_requests",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("request_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("object_type_id", UUID, nullable=False),
        sa.Column("model", sa.String(255)),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(15, 2)),
        sa.Column("currency", sa.String(10)),
        sa.Column("justification", sa.Text()),
        sa.Column("preferred_vendor", sa.String(255)),
        sa.Column("items", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("workflow_instance_id", UUID),
        sa.Column("requester_id", UUID, nullable=False),
        sa.Column("approved_by", UUID),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("rejected_by", UUID),
        sa.Column("rejected_at", sa.DateTime()),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["object_type_id"], ["object_types.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["rejected_by"], ["users.id"]),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_requests_quantity"),
        sa.CheckConstraint("status IN ('DRAFT','PENDING','APPROVED','REJECTED','CANCELLED')", name="ck_purchase_requests_status"),
    )
    op.create_index("idx_purchase_requests_requester", "purchase_requests", ["requester_id", "status"])
    op.create_index("idx_purchase_requests_status", "purchase_requests", ["status", "created_at"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("order_number", sa.String(100), nullable=False, unique=True),
        sa.Column("purchase_request_id", UUID),
        sa.Column("vendor", sa.String(255), nullable=False),
        sa.Column("contract_number", sa.String(255)),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("expected_delivery_date", sa.Date()),
        sa.Column("actual_delivery_date", sa.Date()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", UUID),
        sa.ForeignKeyConstraint(["purchase_request_id"], ["purchase_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint("status IN ('CREATED','SENT','CONFIRMED','SHIPPED','RECEIVED','CANCELLED')", name="ck_purchase_orders_status"),
    )
    op.create_index("idx_purchase_orders_vendor", "purchase_orders", ["vendor", "status"])
    op.create_index("idx_purchase_orders_delivery", "purchase_orders", ["expected_delivery_date"], postgresql_where=sa.text("status != 'RECEIVED'"))

    op.create_table(
        "inventory_locations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("warehouse", sa.String(255), nullable=False),
        sa.Column("shelf", sa.String(100)),
        sa.Column("location_code", sa.String(100), nullable=False, unique=True),
        sa.Column("organization_id", UUID),
        sa.Column("description", sa.Text()),
        sa.Column("deleted_at", sa.DateTime()),
        sa.Column("deleted_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
    )
    op.create_index("idx_inventory_locations_org", "inventory_locations", ["organization_id"])
    op.create_index("idx_inventory_locations_active", "inventory_locations", ["id"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "assets",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("object_id", UUID, nullable=False, unique=True),
        sa.Column("asset_number", sa.String(255), nullable=False, unique=True),
        sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="REQUESTED"),
        sa.Column("purchase_request_id", UUID),
        sa.Column("purchase_order_id", UUID),
        sa.Column("purchase_date", sa.Date()),
        sa.Column("received_date", sa.Date()),
        sa.Column("vendor", sa.String(255)),
        sa.Column("contract_number", sa.String(255)),
        sa.Column("warranty_start_date", sa.Date()),
        sa.Column("warranty_end_date", sa.Date()),
        sa.Column("warranty_provider", sa.String(255)),
        sa.Column("service_level", sa.String(100)),
        sa.Column("cost", sa.Numeric(15, 2)),
        sa.Column("currency", sa.String(10)),
        sa.Column("owner_org_id", UUID),
        sa.Column("operator_org_id", UUID),
        sa.Column("maintainer_org_id", UUID),
        sa.Column("inventory_location_id", UUID),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime()),
        sa.Column("deleted_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", UUID),
        sa.Column("updated_by", UUID),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["purchase_request_id"], ["purchase_requests.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["owner_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["operator_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["maintainer_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["inventory_location_id"], ["inventory_locations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.CheckConstraint("lifecycle_status IN ('REQUESTED','APPROVED','ORDERED','PURCHASED','RECEIVED','STOCK','IN_TRANSIT','DEPLOYING','DEPLOYED','ACTIVE','MAINTENANCE','TRANSFERRED','RETIRED','RECOVERED')", name="ck_assets_lifecycle_status"),
    )
    op.create_index("idx_assets_object", "assets", ["object_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_assets_status", "assets", ["lifecycle_status"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_assets_owner_org", "assets", ["owner_org_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_assets_operator_org", "assets", ["operator_org_id"])
    op.create_index("idx_assets_maintainer_org", "assets", ["maintainer_org_id"])
    op.create_index("idx_assets_inventory_location", "assets", ["inventory_location_id"])
    op.create_index("idx_assets_vendor", "assets", ["vendor"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_assets_warranty", "assets", ["warranty_end_date"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_assets_active", "assets", ["id"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "deployments",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("asset_id", UUID, nullable=False),
        sa.Column("object_id", UUID, nullable=False),
        sa.Column("location_id", UUID, nullable=False),
        sa.Column("deployment_type", sa.String(50), nullable=False, server_default="NEW"),
        sa.Column("status", sa.String(50), nullable=False, server_default="PLANNED"),
        sa.Column("acceptance_status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("deployed_by", UUID),
        sa.Column("deployed_at", sa.DateTime()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["deployed_by"], ["users.id"]),
        sa.CheckConstraint("deployment_type IN ('NEW','TRANSFER','REPLACEMENT')", name="ck_deployments_type"),
        sa.CheckConstraint("status IN ('PLANNED','IN_PROGRESS','COMPLETED','FAILED')", name="ck_deployments_status"),
        sa.CheckConstraint("acceptance_status IN ('PENDING','ACCEPTED','REJECTED')", name="ck_deployments_acceptance"),
    )
    op.create_index("idx_deployments_asset", "deployments", ["asset_id", "deployed_at"])
    op.create_index("idx_deployments_location", "deployments", ["location_id"], postgresql_where=sa.text("status = 'COMPLETED'"))

    op.create_table(
        "inventory_records",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("asset_id", UUID, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("warehouse_location", sa.String(255)),
        sa.Column("inventory_location_id", UUID),
        sa.Column("related_purchase_order_id", UUID),
        sa.Column("related_deployment_id", UUID),
        sa.Column("operator_id", UUID, nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["inventory_location_id"], ["inventory_locations.id"]),
        sa.ForeignKeyConstraint(["related_purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["related_deployment_id"], ["deployments.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.CheckConstraint("transaction_type IN ('IN','OUT','TRANSFER','ADJUSTMENT')", name="ck_inventory_records_type"),
        sa.CheckConstraint("quantity <> 0", name="ck_inventory_records_quantity"),
    )
    op.create_index("idx_inventory_records_asset", "inventory_records", ["asset_id", "created_at"])
    op.create_index("idx_inventory_records_type", "inventory_records", ["transaction_type", "created_at"])


def downgrade() -> None:
    op.drop_table("inventory_records")
    op.drop_table("deployments")
    op.drop_table("assets")
    op.drop_table("inventory_locations")
    op.drop_table("purchase_orders")
    op.drop_table("purchase_requests")
