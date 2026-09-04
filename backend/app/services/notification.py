"""Transactional helpers for in-app notifications."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Notification


def notify(
    db: Session,
    recipient_id: UUID,
    type: str,
    title: str,
    message: str,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> Notification:
    """Add a notification to the caller's transaction without committing it."""
    item = Notification(
        recipient_id=recipient_id,
        type=type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(item)
    return item
