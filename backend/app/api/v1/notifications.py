"""Authenticated user's in-app notification APIs."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.core.security import require_current_user
from app.database.session import get_db
from app.models import Notification, User


router = APIRouter(prefix="/notifications", tags=["notifications"])


def notification_out(item: Notification) -> dict:
    return {
        "id": item.id, "recipient_id": item.recipient_id, "type": item.type,
        "title": item.title, "message": item.message,
        "entity_type": item.entity_type, "entity_id": item.entity_id,
        "is_read": item.is_read, "read_at": item.read_at,
        "created_at": item.created_at,
    }


@router.get("/my")
def my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_current_user),
):
    active = select(Notification).where(
        Notification.recipient_id == user.id, Notification.deleted_at.is_(None)
    )
    total = db.scalar(select(func.count()).select_from(active.subquery())) or 0
    items = db.scalars(
        active.order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": [notification_out(item) for item in items]}


@router.get("/my/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(require_current_user)):
    count = db.scalar(select(func.count()).select_from(Notification).where(
        Notification.recipient_id == user.id,
        Notification.is_read.is_(False), Notification.deleted_at.is_(None),
    )) or 0
    return {"count": count}


@router.put("/{notification_id}/read")
def mark_read(notification_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_current_user)):
    item = db.scalar(select(Notification).where(
        Notification.id == notification_id,
        Notification.recipient_id == user.id,
        Notification.deleted_at.is_(None),
    ))
    if item is None:
        raise ServiceError(404, "NotificationNotFound", "通知不存在")
    if not item.is_read:
        item.is_read = True
        item.read_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(item)
    return notification_out(item)


@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(require_current_user)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = db.execute(update(Notification).where(
        Notification.recipient_id == user.id,
        Notification.is_read.is_(False), Notification.deleted_at.is_(None),
    ).values(is_read=True, read_at=now))
    db.commit()
    return {"updated": result.rowcount}
