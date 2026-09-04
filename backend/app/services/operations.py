"""Transactional work-order lifecycle business logic."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models import (FaultRecord, InfrastructureObject, ObjectHistory, RepairRecord,
                        ReplacementEvent, User, WorkOrder)
from app.schemas.operations import RepairCreate, ReplacementCreate, WorkOrderCreate
from app.services.core import _operator

ALLOWED_TRANSITIONS = {
    "CREATED": {"ASSIGNED", "CANCELLED"},
    "ASSIGNED": {"PROCESSING", "SUSPENDED", "CANCELLED"},
    "PROCESSING": {"WAITING", "SUSPENDED", "RESOLVED"},
    "WAITING": {"PROCESSING"},
    "SUSPENDED": {"ASSIGNED", "CANCELLED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": {"REOPENED"},
    "REOPENED": {"ASSIGNED", "PROCESSING"},
    "CANCELLED": set(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _number() -> str:
    return f"WO-{datetime.now():%Y%m%d}-{uuid4().hex[:8].upper()}"


def required_user(db: Session, explicit: UUID | None, header_user: str | None, role: str) -> UUID:
    user_id = explicit or _operator(header_user)
    if user_id is None:
        raise ServiceError(422, "UserRequired", f"必须提供{role}用户 ID")
    if db.scalar(select(User.id).where(User.id == user_id, User.deleted_at.is_(None), User.is_active.is_(True))) is None:
        raise ServiceError(422, "InvalidUser", f"{role}用户不存在或已停用")
    return user_id


def active_work_order(db: Session, work_order_id: UUID) -> WorkOrder:
    item = db.scalar(select(WorkOrder).where(WorkOrder.id == work_order_id, WorkOrder.deleted_at.is_(None)))
    if item is None:
        raise ServiceError(404, "WorkOrderNotFound", "工单不存在")
    return item


def require_object(db: Session, object_id: UUID | None) -> InfrastructureObject | None:
    if object_id is None:
        return None
    obj = db.scalar(select(InfrastructureObject).where(InfrastructureObject.id == object_id, InfrastructureObject.deleted_at.is_(None)))
    if obj is None:
        raise ServiceError(404, "ObjectNotFound", "对象不存在")
    return obj


def transition(item: WorkOrder, target: str, operator: UUID, **changes: Any) -> None:
    if target not in ALLOWED_TRANSITIONS.get(item.status, set()):
        raise ServiceError(409, "InvalidWorkOrderTransition", f"工单状态 {item.status} 不能转换为 {target}")
    item.status = target
    item.version += 1
    item.updated_at = _now()
    for field, value in changes.items():
        setattr(item, field, value)


def create_work_order(db: Session, payload: WorkOrderCreate, header_user: str | None) -> WorkOrder:
    creator = required_user(db, None, header_user, "创建人")
    object_id = payload.related_object_id or payload.object_id
    require_object(db, object_id)
    if payload.fault_record_id is not None and db.get(FaultRecord, payload.fault_record_id) is None:
        raise ServiceError(404, "FaultRecordNotFound", "故障记录不存在")
    item = WorkOrder(work_order_number=_number(), title=payload.title, type=payload.type,
                     priority=payload.priority, status="CREATED", related_object_id=object_id,
                     description=payload.description, fault_record_id=payload.fault_record_id, created_by=creator)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def assign(db: Session, item: WorkOrder, assignee: UUID, header_user: str | None) -> WorkOrder:
    required_user(db, None, header_user, "操作人")
    engineer = required_user(db, assignee, None, "处理人")
    transition(item, "ASSIGNED", engineer, assigned_to=engineer, assigned_at=_now())
    db.commit(); db.refresh(item)
    return item


def simple_transition(db: Session, item: WorkOrder, target: str, header_user: str | None) -> WorkOrder:
    operator = required_user(db, None, header_user, "操作人")
    changes: dict[str, Any] = {}
    if target == "RESOLVED": changes = {"resolved_by": operator, "resolved_at": _now()}
    if target == "CLOSED": changes = {"closed_by": operator, "closed_at": _now()}
    transition(item, target, operator, **changes)
    db.commit(); db.refresh(item)
    return item


def add_repair(db: Session, item: WorkOrder, payload: RepairCreate, header_user: str | None) -> RepairRecord:
    if item.status == "ASSIGNED":
        operator = required_user(db, None, header_user, "操作人")
        transition(item, "PROCESSING", operator)
    elif item.status != "PROCESSING":
        raise ServiceError(409, "InvalidWorkOrderTransition", f"工单状态 {item.status} 不能记录维修")
    engineer = required_user(db, payload.engineer_id, header_user, "维修工程师")
    object_id = payload.object_id or item.related_object_id
    if object_id is None:
        raise ServiceError(422, "ObjectRequired", "维修记录必须关联对象")
    require_object(db, object_id)
    record = RepairRecord(work_order_id=item.id, object_id=object_id, repair_type=payload.repair_type,
                          description=payload.description, parts_used=payload.parts_used,
                          repair_result=payload.repair_result, engineer_id=engineer,
                          started_at=payload.started_at or _now(), completed_at=payload.completed_at,
                          verification_notes=payload.verification_notes)
    db.add(record); db.commit(); db.refresh(record)
    return record


def add_replacement(db: Session, item: WorkOrder, payload: ReplacementCreate, header_user: str | None) -> ReplacementEvent:
    if item.status != "PROCESSING":
        raise ServiceError(409, "InvalidWorkOrderTransition", f"工单状态 {item.status} 不能记录部件更换")
    engineer = required_user(db, payload.engineer_id, header_user, "更换工程师")
    old_obj, new_obj = require_object(db, payload.old_object_id), require_object(db, payload.new_object_id)
    if old_obj.id == new_obj.id:
        raise ServiceError(422, "InvalidReplacement", "新旧部件不能是同一对象")
    repair = db.get(RepairRecord, payload.repair_record_id) if payload.repair_record_id else db.scalar(
        select(RepairRecord).where(RepairRecord.work_order_id == item.id).order_by(RepairRecord.created_at.desc()))
    if repair is None or repair.work_order_id != item.id:
        raise ServiceError(422, "InvalidRepairRecord", "更换事件必须关联当前工单的维修记录")
    previous = old_obj.status
    old_obj.status = "MAINTENANCE"
    old_obj.version += 1
    old_obj.updated_by = engineer
    db.add(ObjectHistory(object_id=old_obj.id, change_type="STATUS_CHANGE", before_data={"status": previous},
                         after_data={"status": "MAINTENANCE", "work_order_id": str(item.id)},
                         source="API", confidence="HIGH", operator=engineer))
    event = ReplacementEvent(repair_record_id=repair.id, old_object_id=old_obj.id, new_object_id=new_obj.id,
                             replacement_reason=payload.replacement_reason,
                             old_object_disposition=payload.old_object_disposition, engineer_id=engineer,
                             replaced_at=payload.replaced_at or _now(), notes=payload.notes)
    db.add(event); db.commit(); db.refresh(event)
    return event


def model_out(item: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(item, field) for field in fields}


WORK_ORDER_FIELDS = ("id", "work_order_number", "title", "type", "priority", "status", "related_object_id",
                     "description", "fault_record_id", "assigned_to", "created_by", "resolved_by", "closed_by",
                     "assigned_at", "resolved_at", "closed_at", "version", "created_at", "updated_at")
REPAIR_FIELDS = ("id", "work_order_id", "object_id", "repair_type", "description", "parts_used", "repair_result",
                 "engineer_id", "started_at", "completed_at", "verification_notes", "created_at", "updated_at")
REPLACEMENT_FIELDS = ("id", "repair_record_id", "old_object_id", "new_object_id", "replacement_reason",
                      "old_object_disposition", "engineer_id", "replaced_at", "notes", "created_at")


def detail(db: Session, item: WorkOrder) -> dict[str, Any]:
    repairs = db.scalars(select(RepairRecord).where(RepairRecord.work_order_id == item.id).order_by(RepairRecord.created_at)).all()
    repair_ids = [record.id for record in repairs]
    replacements = db.scalars(select(ReplacementEvent).where(ReplacementEvent.repair_record_id.in_(repair_ids)).order_by(ReplacementEvent.created_at)).all() if repair_ids else []
    result = model_out(item, WORK_ORDER_FIELDS)
    result["repairs"] = [model_out(record, REPAIR_FIELDS) for record in repairs]
    result["replacements"] = [model_out(event, REPLACEMENT_FIELDS) for event in replacements]
    result["timeline"] = timeline(db, item, repairs, replacements)
    return result


def timeline(db: Session, item: WorkOrder, repairs=None, replacements=None) -> list[dict[str, Any]]:
    repairs = repairs if repairs is not None else db.scalars(select(RepairRecord).where(RepairRecord.work_order_id == item.id)).all()
    repair_ids = [r.id for r in repairs]
    replacements = replacements if replacements is not None else (db.scalars(select(ReplacementEvent).where(ReplacementEvent.repair_record_id.in_(repair_ids))).all() if repair_ids else [])
    events = [{"type": "STATUS", "status": "CREATED", "at": item.created_at, "operator_id": item.created_by}]
    if item.assigned_at: events.append({"type": "STATUS", "status": "ASSIGNED", "at": item.assigned_at, "operator_id": item.assigned_to})
    if repairs:
        first_repair = min(repairs, key=lambda record: record.started_at)
        events.append({"type": "STATUS", "status": "PROCESSING", "at": first_repair.started_at, "operator_id": first_repair.engineer_id})
    for record in repairs: events.append({"type": "REPAIR", "record_id": record.id, "at": record.created_at, "operator_id": record.engineer_id})
    for event in replacements: events.append({"type": "REPLACEMENT", "record_id": event.id, "at": event.created_at, "operator_id": event.engineer_id})
    if item.resolved_at: events.append({"type": "STATUS", "status": "RESOLVED", "at": item.resolved_at, "operator_id": item.resolved_by})
    if item.closed_at: events.append({"type": "STATUS", "status": "CLOSED", "at": item.closed_at, "operator_id": item.closed_by})
    return sorted(events, key=lambda event: event["at"])
