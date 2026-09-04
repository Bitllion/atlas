"""In-app notification persistence model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin


class Notification(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index(
            "idx_notifications_recipient_unread_created",
            "recipient_id", "is_read", text("created_at DESC"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    recipient_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[UUID | None]
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    read_at: Mapped[datetime | None]
