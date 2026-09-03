"""Audit and request-idempotency persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin


class AuditLog(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_user", "user_id", text("created_at DESC")),
        Index("idx_audit_logs_resource", "resource_type", "resource_id", text("created_at DESC")),
        Index("idx_audit_logs_action", "action", text("created_at DESC")),
        Index("idx_audit_logs_time", text("created_at DESC")),
        Index("idx_audit_logs_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[UUID | None]
    before_data: Mapped[dict | None] = mapped_column(JSONB)
    after_data: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)


class IdempotencyKey(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        Index("idx_idempotency_keys_key", "idempotency_key"),
        Index("idx_idempotency_keys_expires", "expires_at"),
        Index("idx_idempotency_keys_user", "user_id"),
        Index("idx_idempotency_keys_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)
    endpoint: Mapped[str] = mapped_column(String(500))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_status: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[dict | None] = mapped_column(JSONB)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime]
