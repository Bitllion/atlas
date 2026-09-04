"""Generic workflow definition, instance, and approval-task models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, SoftDeleteMixin, TimestampMixin


class WorkflowDefinition(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "workflow_definition"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_workflow_definition_version"),
        Index("idx_workflow_definition_active", "is_active", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(255), unique=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    definition: Mapped[dict] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class WorkflowInstance(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "workflow_instance"
    __table_args__ = (
        CheckConstraint("status IN ('RUNNING','COMPLETED','TERMINATED')", name="ck_workflow_instance_status"),
        CheckConstraint("version > 0", name="ck_workflow_instance_version"),
        Index("idx_workflow_instance_entity", "entity_type", "entity_id"),
        Index("idx_workflow_instance_status", "status", text("started_at DESC"), postgresql_where=text("deleted_at IS NULL")),
    )

    definition_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_definition.id"))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[UUID]
    business_key: Mapped[str | None] = mapped_column(String(255))
    current_node_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", server_default="RUNNING")
    started_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class WorkflowTask(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "workflow_task"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','APPROVED','REJECTED','SKIPPED')", name="ck_workflow_task_status"),
        Index("idx_workflow_task_instance", "instance_id", "created_at"),
        Index("idx_workflow_task_assignee", "assignee_id", "status", postgresql_where=text("status = 'PENDING' AND deleted_at IS NULL")),
    )

    instance_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_instance.id", ondelete="CASCADE"))
    node_id: Mapped[str] = mapped_column(String(100))
    assignee_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(50), default="PENDING", server_default="PENDING")
    comment: Mapped[str | None] = mapped_column(Text)
    actioned_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    actioned_at: Mapped[datetime | None]
