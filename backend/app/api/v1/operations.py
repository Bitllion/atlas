"""HTTP routes for Phase 4a operations management."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import actor_id, get_current_user_optional
from app.models import User, WorkOrder
from app.schemas.operations import RepairCreate, ReplacementCreate, WorkOrderAssign, WorkOrderCreate
from app.services import operations as service

router = APIRouter(tags=["operations"])


@router.post("/work-orders", status_code=status.HTTP_201_CREATED)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.model_out(service.create_work_order(db, payload, actor_id(user)), service.WORK_ORDER_FIELDS)


@router.put("/work-orders/{work_order_id}/assign")
def assign_work_order(work_order_id: UUID, payload: WorkOrderAssign, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    assignee = payload.assigned_to or payload.assignee_id
    if assignee is None:
        from app.core.exceptions import ServiceError
        raise ServiceError(422, "AssigneeRequired", "必须提供处理人 ID")
    item = service.assign(db, service.active_work_order(db, work_order_id), assignee, actor_id(user))
    return service.model_out(item, service.WORK_ORDER_FIELDS)


@router.put("/work-orders/{work_order_id}/start")
def start_work_order(work_order_id: UUID, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    item = service.simple_transition(db, service.active_work_order(db, work_order_id), "PROCESSING", actor_id(user))
    return service.model_out(item, service.WORK_ORDER_FIELDS)


@router.post("/work-orders/{work_order_id}/repairs", status_code=status.HTTP_201_CREATED)
def add_repair(work_order_id: UUID, payload: RepairCreate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    record = service.add_repair(db, service.active_work_order(db, work_order_id), payload, actor_id(user))
    return service.model_out(record, service.REPAIR_FIELDS)


@router.post("/work-orders/{work_order_id}/replacements", status_code=status.HTTP_201_CREATED)
def add_replacement(work_order_id: UUID, payload: ReplacementCreate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    event = service.add_replacement(db, service.active_work_order(db, work_order_id), payload, actor_id(user))
    return service.model_out(event, service.REPLACEMENT_FIELDS)


@router.put("/work-orders/{work_order_id}/resolve")
def resolve_work_order(work_order_id: UUID, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    item = service.simple_transition(db, service.active_work_order(db, work_order_id), "RESOLVED", actor_id(user))
    return service.model_out(item, service.WORK_ORDER_FIELDS)


@router.put("/work-orders/{work_order_id}/close")
def close_work_order(work_order_id: UUID, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    item = service.simple_transition(db, service.active_work_order(db, work_order_id), "CLOSED", actor_id(user))
    return service.model_out(item, service.WORK_ORDER_FIELDS)


def _list(db: Session, work_order_status: str | None, work_order_type: str | None, object_id: UUID | None, page: int, page_size: int):
    query = select(WorkOrder).where(WorkOrder.deleted_at.is_(None))
    if work_order_status: query = query.where(WorkOrder.status == work_order_status)
    if work_order_type: query = query.where(WorkOrder.type == work_order_type)
    if object_id: query = query.where(WorkOrder.related_object_id == object_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(WorkOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [service.model_out(item, service.WORK_ORDER_FIELDS) for item in items]}


@router.get("/work-orders")
def list_work_orders(work_order_status: str | None = Query(default=None, alias="status"), work_order_type: str | None = Query(default=None, alias="type"), object_id: UUID | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    return _list(db, work_order_status, work_order_type, object_id, page, page_size)


@router.get("/work-orders/{work_order_id}")
def get_work_order(work_order_id: UUID, db: Session = Depends(get_db)):
    return service.detail(db, service.active_work_order(db, work_order_id))


@router.get("/work-orders/{work_order_id}/timeline")
def get_work_order_timeline(work_order_id: UUID, db: Session = Depends(get_db)):
    item = service.active_work_order(db, work_order_id)
    return {"work_order_id": item.id, "items": service.timeline(db, item)}


@router.get("/objects/{object_id}/work-orders")
def get_object_work_orders(object_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    service.require_object(db, object_id)
    return _list(db, None, None, object_id, page, page_size)
