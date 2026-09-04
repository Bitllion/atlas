"""Operations work-order, fault, repair, and replacement models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin


class WorkOrder(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint("type IN ('FAULT','REPAIR','INSPECTION','CHANGE')", name="ck_work_orders_type"),
        CheckConstraint("priority IN ('CRITICAL','HIGH','MEDIUM','LOW')", name="ck_work_orders_priority"),
        CheckConstraint("status IN ('CREATED','ASSIGNED','PROCESSING','WAITING','SUSPENDED','RESOLVED','CLOSED','CANCELLED','REOPENED')", name="ck_work_orders_status"),
        Index("idx_work_orders_assigned", "assigned_to", "status", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_work_orders_object", "related_object_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_work_orders_status", "status", "priority", text("created_at DESC"), postgresql_where=text("deleted_at IS NULL")),
    )
    work_order_number: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="CREATED", server_default="CREATED")
    related_object_id: Mapped[UUID | None] = mapped_column(ForeignKey("objects.id"))
    description: Mapped[str | None] = mapped_column(Text)
    fault_record_id: Mapped[UUID | None] = mapped_column(ForeignKey("fault_records.id", use_alter=True, name="fk_work_orders_fault_record"))
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    resolved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    closed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime | None]
    resolved_at: Mapped[datetime | None]
    closed_at: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class FaultRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "fault_records"
    __table_args__ = (
        CheckConstraint("fault_type IN ('HARDWARE','SOFTWARE','NETWORK','COOLING','POWER')", name="ck_fault_records_type"),
        CheckConstraint("severity IN ('CRITICAL','HIGH','MEDIUM','LOW')", name="ck_fault_records_severity"),
        Index("idx_fault_records_object", "object_id", text("detected_at DESC")),
        Index("idx_fault_records_severity", "severity", text("detected_at DESC")),
    )
    object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    fault_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    symptoms: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(100))
    detected_at: Mapped[datetime]
    reported_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class RepairRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "repair_records"
    __table_args__ = (
        CheckConstraint("repair_type IN ('REPLACEMENT','UPGRADE','ADJUSTMENT','CLEANING')", name="ck_repair_records_type"),
        CheckConstraint("repair_result IN ('SUCCESS','FAILED','PARTIAL')", name="ck_repair_records_result"),
        Index("idx_repair_records_workorder", "work_order_id"),
        Index("idx_repair_records_object", "object_id", text("completed_at DESC")),
    )
    work_order_id: Mapped[UUID] = mapped_column(ForeignKey("work_orders.id"))
    object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    repair_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    parts_used: Mapped[list | None] = mapped_column(JSONB)
    repair_result: Mapped[str] = mapped_column(String(50))
    engineer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
    verification_notes: Mapped[str | None] = mapped_column(Text)


class ReplacementEvent(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "replacement_events"
    __table_args__ = (
        CheckConstraint("replacement_reason IN ('FAILURE','UPGRADE','PREVENTIVE')", name="ck_replacement_events_reason"),
        CheckConstraint("old_object_disposition IN ('RETIRED','RMA','STOCK','SCRAPPED')", name="ck_replacement_events_disposition"),
        Index("idx_replacement_events_old", "old_object_id", text("replaced_at DESC")),
        Index("idx_replacement_events_new", "new_object_id"),
    )
    repair_record_id: Mapped[UUID | None] = mapped_column(ForeignKey("repair_records.id"))
    old_object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    new_object_id: Mapped[UUID] = mapped_column(ForeignKey("objects.id"))
    replacement_reason: Mapped[str] = mapped_column(String(255))
    old_object_disposition: Mapped[str] = mapped_column(String(100))
    engineer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    replaced_at: Mapped[datetime]
    notes: Mapped[str | None] = mapped_column(Text)
