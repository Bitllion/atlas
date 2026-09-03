"""Infrastructure object, specification, relationship, and history models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin


class ObjectType(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "object_types"
    __table_args__ = (
        CheckConstraint("category IN ('IT', 'NETWORK', 'FACILITY', 'POWER')", name="ck_object_types_category"),
        Index("idx_object_types_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    schema: Mapped[dict | None] = mapped_column(JSONB)


class RelationshipType(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "relationship_types"
    __table_args__ = (
        Index("idx_relationship_types_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_directed: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    allowed_source_types: Mapped[list | None] = mapped_column(JSONB)
    allowed_target_types: Mapped[list | None] = mapped_column(JSONB)
    attributes_schema: Mapped[dict | None] = mapped_column(JSONB)


class InfrastructureObject(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "objects"
    __table_args__ = (
        CheckConstraint("status IN ('PLANNED', 'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'RETIRED')", name="ck_objects_status"),
        CheckConstraint("ownership IN ('OWNED', 'CUSTOMER_OWNED', 'THIRD_PARTY')", name="ck_objects_ownership"),
        CheckConstraint("management_scope IN ('FULL_CONTROL', 'HARDWARE_ONLY', 'MAINTENANCE_ONLY', 'NO_ACCESS')", name="ck_objects_management_scope"),
        Index("idx_objects_type_status", "object_type_id", "status", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_objects_owner_org", "owner_org_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_objects_operator_org", "operator_org_id"),
        Index("idx_objects_maintainer_org", "maintainer_org_id"),
        Index("idx_objects_deployed_location", "deployed_location_id"),
        Index("idx_objects_created_by", "created_by"),
        Index("idx_objects_updated_by", "updated_by"),
        Index("idx_objects_serial", "serial_number", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_objects_firmware", "firmware_version", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_objects_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    object_type_id: Mapped[UUID] = mapped_column(ForeignKey("object_types.id"))
    name: Mapped[str] = mapped_column(String(255))
    serial_number: Mapped[str | None] = mapped_column(String(255))
    asset_number: Mapped[str | None] = mapped_column(String(255))
    uuid: Mapped[str | None] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str | None] = mapped_column(String(255))
    firmware_version: Mapped[str | None] = mapped_column(String(100))
    hardware_generation: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", server_default="PLANNED")
    ownership: Mapped[str] = mapped_column(String(50))
    management_scope: Mapped[str] = mapped_column(String(50))
    owner_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    operator_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    maintainer_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    deployed_location_id: Mapped[UUID | None] = mapped_column(ForeignKey("objects.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class ObjectSpec(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "object_specs"
    __table_args__ = (
        CheckConstraint("data_source IN ('DISCOVERY', 'MANUAL', 'IMPORT', 'DOCUMENT', 'CUSTOMER_REPORT', 'VENDOR')", name="ck_object_specs_data_source"),
        CheckConstraint("confidence IN ('HIGH', 'MEDIUM', 'LOW')", name="ck_object_specs_confidence"),
        CheckConstraint("data_status IN ('FRESH', 'NORMAL', 'STALE', 'UNKNOWN', 'INVALID')", name="ck_object_specs_data_status"),
        Index("idx_object_specs_object", "object_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_object_specs_data", "spec_data", postgresql_using="gin"),
        Index("idx_object_specs_status", "data_status", "last_successful_update"),
        Index("idx_object_specs_operator", "operator_id"),
        Index("idx_object_specs_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    spec_data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    data_source: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[str] = mapped_column(String(50))
    data_status: Mapped[str] = mapped_column(String(50))
    operator_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    last_successful_update: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class ObjectRelationship(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "relationships"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'REMOVED')", name="ck_relationships_status"),
        CheckConstraint("confidence IN ('HIGH', 'MEDIUM', 'LOW')", name="ck_relationships_confidence"),
        Index("idx_relationships_source", "source_object_id", "relation_type_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_relationships_target", "target_object_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_relationships_type", "relation_type_id", "status", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_relationships_verified_by", "verified_by"),
        Index("idx_relationships_created_by", "created_by"),
        Index("idx_relationships_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    source_object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    relation_type_id: Mapped[UUID] = mapped_column(ForeignKey("relationship_types.id"))
    target_object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    attributes: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", server_default="ACTIVE")
    confidence: Mapped[str] = mapped_column(String(50))
    data_source: Mapped[str] = mapped_column(String(100))
    verified_at: Mapped[datetime | None]
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class ObjectHistory(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "object_history"
    __table_args__ = (
        CheckConstraint("change_type IN ('CREATE', 'UPDATE', 'DELETE', 'STATUS_CHANGE', 'LOCATION_CHANGE')", name="ck_object_history_change_type"),
        CheckConstraint("source IN ('DISCOVERY', 'MANUAL', 'IMPORT', 'API')", name="ck_object_history_source"),
        CheckConstraint("confidence IS NULL OR confidence IN ('HIGH', 'MEDIUM', 'LOW')", name="ck_object_history_confidence"),
        Index("idx_object_history_object", "object_id", text("created_at DESC")),
        Index("idx_object_history_time", "created_at", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_object_history_operator", "operator"),
        Index("idx_object_history_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    change_type: Mapped[str] = mapped_column(String(100))
    before_data: Mapped[dict | None] = mapped_column(JSONB)
    after_data: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[str | None] = mapped_column(String(50))
    operator: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
