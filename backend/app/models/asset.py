"""Asset procurement, inventory, and deployment persistence models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin


class PurchaseRequest(IdMixin, TimestampMixin, Base):
    __tablename__ = "purchase_requests"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_requests_quantity"),
        CheckConstraint("status IN ('DRAFT','PENDING','APPROVED','REJECTED','CANCELLED')", name="ck_purchase_requests_status"),
        Index("idx_purchase_requests_requester", "requester_id", "status"),
        Index("idx_purchase_requests_status", "status", "created_at"),
    )
    request_number: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    object_type_id: Mapped[UUID] = mapped_column(ForeignKey("object_types.id"))
    model: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    justification: Mapped[str | None] = mapped_column(Text)
    preferred_vendor: Mapped[str | None] = mapped_column(String(255))
    items: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String(50), default="PENDING", server_default="PENDING")
    workflow_instance_id: Mapped[UUID | None]
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None]
    rejected_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    rejected_at: Mapped[datetime | None]
    rejection_reason: Mapped[str | None] = mapped_column(Text)


class PurchaseOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("idx_purchase_orders_vendor", "vendor", "status"),
        Index("idx_purchase_orders_delivery", "expected_delivery_date", postgresql_where=text("status != 'RECEIVED'")),
    )
    order_number: Mapped[str] = mapped_column(String(100), unique=True)
    purchase_request_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_requests.id"))
    vendor: Mapped[str] = mapped_column(String(255))
    contract_number: Mapped[str | None] = mapped_column(String(255))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(50))
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class InventoryLocation(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "inventory_locations"
    __table_args__ = (
        Index("idx_inventory_locations_org", "organization_id"),
        Index("idx_inventory_locations_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )
    name: Mapped[str] = mapped_column(String(255))
    warehouse: Mapped[str] = mapped_column(String(255))
    shelf: Mapped[str | None] = mapped_column(String(100))
    location_code: Mapped[str] = mapped_column(String(100), unique=True)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    description: Mapped[str | None] = mapped_column(Text)


class Asset(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint("lifecycle_status IN ('REQUESTED','APPROVED','ORDERED','PURCHASED','RECEIVED','STOCK','IN_TRANSIT','DEPLOYING','DEPLOYED','ACTIVE','MAINTENANCE','TRANSFERRED','RETIRED','RECOVERED')", name="ck_assets_lifecycle_status"),
        Index("idx_assets_status", "lifecycle_status", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_assets_owner_org", "owner_org_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_assets_object", "object_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_assets_operator_org", "operator_org_id"),
        Index("idx_assets_maintainer_org", "maintainer_org_id"),
        Index("idx_assets_inventory_location", "inventory_location_id"),
        Index("idx_assets_vendor", "vendor", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_assets_warranty", "warranty_end_date", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_assets_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )
    object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"), unique=True)
    asset_number: Mapped[str] = mapped_column(String(255), unique=True)
    lifecycle_status: Mapped[str] = mapped_column(String(50), default="REQUESTED", server_default="REQUESTED")
    purchase_request_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_requests.id"))
    purchase_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_orders.id"))
    purchase_date: Mapped[date | None] = mapped_column(Date)
    received_date: Mapped[date | None] = mapped_column(Date)
    vendor: Mapped[str | None] = mapped_column(String(255))
    contract_number: Mapped[str | None] = mapped_column(String(255))
    warranty_start_date: Mapped[date | None] = mapped_column(Date)
    warranty_end_date: Mapped[date | None] = mapped_column(Date)
    warranty_provider: Mapped[str | None] = mapped_column(String(255))
    service_level: Mapped[str | None] = mapped_column(String(100))
    cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    owner_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    operator_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    maintainer_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    inventory_location_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_locations.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class Deployment(IdMixin, TimestampMixin, Base):
    __tablename__ = "deployments"
    __table_args__ = (
        Index("idx_deployments_asset", "asset_id", "deployed_at"),
        Index("idx_deployments_location", "location_id", postgresql_where=text("status = 'COMPLETED'")),
    )
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    location_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    deployment_type: Mapped[str] = mapped_column(String(50), default="NEW", server_default="NEW")
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", server_default="PLANNED")
    acceptance_status: Mapped[str] = mapped_column(String(50), default="PENDING", server_default="PENDING")
    deployed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    deployed_at: Mapped[datetime | None]
    notes: Mapped[str | None] = mapped_column(Text)


class InventoryRecord(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "inventory_records"
    __table_args__ = (
        Index("idx_inventory_records_asset", "asset_id", "created_at"),
        Index("idx_inventory_records_type", "transaction_type", "created_at"),
    )
    transaction_type: Mapped[str] = mapped_column(String(50))
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    warehouse_location: Mapped[str | None] = mapped_column(String(255))
    inventory_location_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_locations.id"))
    related_purchase_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_orders.id"))
    related_deployment_id: Mapped[UUID | None] = mapped_column(ForeignKey("deployments.id"))
    operator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text)
