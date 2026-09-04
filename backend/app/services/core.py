"""Transactional business logic for Infrastructure Core."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models import AuditLog, IdempotencyKey, InfrastructureObject, ObjectHistory, ObjectRelationship, ObjectSpec, ObjectType, RelationshipType, User
from app.schemas.core import ObjectCreate, ObjectUpdate, RelationshipCreate
from app.services.resource_scope import (creation_organizations, has_global_resource_access,
                                         organization_scope, require_organization_write_access)


OBJECT_FIELDS = (
    "id", "object_type_id", "name", "serial_number", "asset_number", "uuid",
    "manufacturer", "model", "firmware_version", "hardware_generation", "status",
    "ownership", "management_scope", "owner_org_id", "operator_org_id",
    "maintainer_org_id", "deployed_location_id", "version", "deleted_at",
)


def _json_value(value: Any) -> Any:
    if isinstance(value, (UUID, datetime)):
        return str(value)
    return value


def _snapshot(obj: InfrastructureObject, spec_data: dict | None = None) -> dict[str, Any]:
    result = {field: _json_value(getattr(obj, field)) for field in OBJECT_FIELDS}
    result["spec_data"] = spec_data or {}
    return result


def _active_object(db: Session, object_id: UUID) -> InfrastructureObject:
    obj = db.scalar(select(InfrastructureObject).where(InfrastructureObject.id == object_id, InfrastructureObject.deleted_at.is_(None)))
    if obj is None:
        raise ServiceError(404, "ObjectNotFound", "对象不存在")
    return obj


def _operator(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError as exc:
        raise ServiceError(400, "InvalidOperator", "X-User-Id 必须是 UUID") from exc


def _audit(db: Session, action: str, resource_type: str, resource_id: UUID, before: dict | None, after: dict | None, operator: UUID | None, ip: str | None, agent: str | None) -> None:
    db.add(AuditLog(user_id=operator, action=action, resource_type=resource_type, resource_id=resource_id, before_data=before, after_data=after, ip_address=ip, user_agent=agent))


def create_object(db: Session, payload: ObjectCreate, user: User, ip: str | None, agent: str | None) -> InfrastructureObject:
    operator = user.id
    if db.scalar(select(ObjectType.id).where(ObjectType.id == payload.object_type_id, ObjectType.deleted_at.is_(None))) is None:
        raise ServiceError(400, "InvalidObjectType", "对象类型不存在")
    values = payload.model_dump(exclude={"spec_data"})
    values["owner_org_id"], values["operator_org_id"] = creation_organizations(
        db, user, payload.owner_org_id, payload.operator_org_id
    )
    obj = InfrastructureObject(**values, created_by=operator, updated_by=operator)
    db.add(obj)
    db.flush()
    spec = ObjectSpec(object_id=obj.id, spec_data=payload.spec_data or {}, data_source="MANUAL", confidence="MEDIUM", data_status="UNKNOWN", operator_id=operator)
    db.add(spec)
    after = _snapshot(obj, spec.spec_data)
    db.add(ObjectHistory(object_id=obj.id, change_type="CREATE", before_data=None, after_data=after, source="API", confidence="MEDIUM", operator=operator))
    _audit(db, "CREATE", "object", obj.id, None, after, operator, ip, agent)
    db.commit()
    db.refresh(obj)
    return obj


def list_objects(db: Session, object_type_id: UUID | None, status: str | None, name: str | None, page: int, page_size: int, user: User) -> tuple[int, list[InfrastructureObject]]:
    filters = [InfrastructureObject.deleted_at.is_(None)]
    if not has_global_resource_access(db, user):
        filters.append(organization_scope(InfrastructureObject, user.organization_id))
    if object_type_id:
        filters.append(InfrastructureObject.object_type_id == object_type_id)
    if status:
        filters.append(InfrastructureObject.status == status)
    if name:
        filters.append(InfrastructureObject.name.ilike(f"%{name}%"))
    total = db.scalar(select(func.count()).select_from(InfrastructureObject).where(*filters)) or 0
    items = list(db.scalars(select(InfrastructureObject).where(*filters).order_by(InfrastructureObject.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))
    return total, items


def object_detail(db: Session, object_id: UUID) -> dict[str, Any]:
    obj = _active_object(db, object_id)
    object_type = db.get(ObjectType, obj.object_type_id)
    spec = db.scalar(select(ObjectSpec).where(ObjectSpec.object_id == obj.id, ObjectSpec.deleted_at.is_(None)))
    outgoing = db.scalar(select(func.count()).select_from(ObjectRelationship).where(ObjectRelationship.source_object_id == obj.id, ObjectRelationship.deleted_at.is_(None))) or 0
    incoming = db.scalar(select(func.count()).select_from(ObjectRelationship).where(ObjectRelationship.target_object_id == obj.id, ObjectRelationship.deleted_at.is_(None))) or 0
    data = {field: getattr(obj, field) for field in Object_FIELDS_OUT}
    data.update(object_type=object_type, spec_data=spec.spec_data if spec else {}, relationship_summary={"outgoing": outgoing, "incoming": incoming, "total": outgoing + incoming})
    return data


Object_FIELDS_OUT = tuple(field for field in OBJECT_FIELDS if field != "deleted_at") + ("created_at", "updated_at")


def idempotency_lookup(db: Session, key: str | None, endpoint: str, body: dict) -> dict | None:
    if not key:
        return None
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    record = db.scalar(select(IdempotencyKey).where(IdempotencyKey.idempotency_key == key, IdempotencyKey.deleted_at.is_(None), IdempotencyKey.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)))
    if record is None:
        return None
    if record.endpoint != endpoint or record.request_hash != digest:
        raise ServiceError(400, "IdempotencyKeyConflict", "相同 Idempotency-Key 不能用于不同请求")
    return {"status": record.response_status, "body": record.response_body}


def idempotency_store(db: Session, key: str | None, endpoint: str, body: dict, status_code: int, response_body: dict | None, user: str | None) -> None:
    if not key:
        return
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    db.add(IdempotencyKey(idempotency_key=key, endpoint=endpoint, request_hash=digest, response_status=status_code, response_body=response_body, user_id=_operator(user), expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)))
    db.commit()


def update_object(db: Session, object_id: UUID, payload: ObjectUpdate, expected: int, user: User, ip: str | None, agent: str | None) -> InfrastructureObject:
    operator = user.id
    obj = _active_object(db, object_id)
    require_organization_write_access(db, user, obj)
    spec = db.scalar(select(ObjectSpec).where(ObjectSpec.object_id == obj.id, ObjectSpec.deleted_at.is_(None)))
    before = _snapshot(obj, spec.spec_data if spec else {})
    values = payload.model_dump(exclude_unset=True, exclude={"version", "spec_data"})
    values.update(version=InfrastructureObject.version + 1, updated_at=func.now(), updated_by=operator)
    result = db.execute(update(InfrastructureObject).where(InfrastructureObject.id == object_id, InfrastructureObject.deleted_at.is_(None), InfrastructureObject.version == expected).values(**values))
    if result.rowcount != 1:
        db.rollback()
        current = db.scalar(select(InfrastructureObject.version).where(InfrastructureObject.id == object_id))
        raise ServiceError(409, "ConcurrentModificationError", "资源已被修改，请刷新后重试", current_version=current, expected_version=expected)
    if "spec_data" in payload.model_fields_set:
        if spec is None:
            spec = ObjectSpec(object_id=obj.id, spec_data=payload.spec_data or {}, data_source="MANUAL", confidence="MEDIUM", data_status="UNKNOWN", operator_id=operator)
            db.add(spec)
        else:
            spec.spec_data = payload.spec_data or {}
            spec.version += 1
            spec.data_source = "MANUAL"
            spec.confidence = "MEDIUM"
            spec.operator_id = operator
            spec.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.flush()
    db.refresh(obj)
    after = _snapshot(obj, spec.spec_data if spec else {})
    db.add(ObjectHistory(object_id=obj.id, change_type="UPDATE", before_data=before, after_data=after, source="API", confidence="MEDIUM", operator=operator))
    _audit(db, "UPDATE", "object", obj.id, before, after, operator, ip, agent)
    db.commit()
    db.refresh(obj)
    return obj


def delete_object(db: Session, object_id: UUID, user: User, ip: str | None, agent: str | None) -> None:
    operator = user.id
    obj = _active_object(db, object_id)
    require_organization_write_access(db, user, obj)
    spec = db.scalar(select(ObjectSpec).where(ObjectSpec.object_id == obj.id, ObjectSpec.deleted_at.is_(None)))
    before = _snapshot(obj, spec.spec_data if spec else {})
    obj.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    obj.deleted_by = operator
    obj.updated_by = operator
    obj.version += 1
    after = _snapshot(obj, spec.spec_data if spec else {})
    db.add(ObjectHistory(object_id=obj.id, change_type="DELETE", before_data=before, after_data=after, source="API", confidence="MEDIUM", operator=operator))
    _audit(db, "DELETE", "object", obj.id, before, after, operator, ip, agent)
    db.commit()


def create_relationship(db: Session, payload: RelationshipCreate, user: User, ip: str | None, agent: str | None) -> ObjectRelationship:
    operator = user.id
    source = _active_object(db, payload.source_object_id)
    target = _active_object(db, payload.target_object_id)
    require_organization_write_access(db, user, source)
    require_organization_write_access(db, user, target)
    relation_type = db.scalar(select(RelationshipType).where(RelationshipType.id == payload.relationship_type_id, RelationshipType.deleted_at.is_(None)))
    if relation_type is None:
        raise ServiceError(400, "InvalidRelationshipType", "关系类型不存在")
    source_type = db.scalar(select(ObjectType.name).where(ObjectType.id == source.object_type_id))
    target_type = db.scalar(select(ObjectType.name).where(ObjectType.id == target.object_type_id))
    if relation_type.allowed_source_types and source_type not in relation_type.allowed_source_types:
        raise ServiceError(400, "InvalidRelationshipSource", "源对象类型不允许使用该关系")
    if relation_type.allowed_target_types and target_type not in relation_type.allowed_target_types:
        raise ServiceError(400, "InvalidRelationshipTarget", "目标对象类型不允许使用该关系")
    values = payload.model_dump(exclude={"relationship_type_id"})
    relation = ObjectRelationship(
        **values,
        relation_type_id=payload.relationship_type_id,
        created_by=operator,
    )
    db.add(relation)
    db.flush()
    after = {key: _json_value(getattr(relation, key)) for key in ("id", "source_object_id", "relation_type_id", "target_object_id", "attributes", "status", "confidence", "data_source")}
    _audit(db, "CREATE", "relationship", relation.id, None, after, operator, ip, agent)
    db.commit()
    db.refresh(relation)
    return relation


def delete_relationship(db: Session, relationship_id: UUID, user: User, ip: str | None, agent: str | None) -> None:
    operator = user.id
    relation = db.scalar(select(ObjectRelationship).where(ObjectRelationship.id == relationship_id, ObjectRelationship.deleted_at.is_(None)))
    if relation is None:
        raise ServiceError(404, "RelationshipNotFound", "关系不存在")
    require_organization_write_access(db, user, _active_object(db, relation.source_object_id))
    require_organization_write_access(db, user, _active_object(db, relation.target_object_id))
    before = {key: _json_value(getattr(relation, key)) for key in ("id", "source_object_id", "relation_type_id", "target_object_id", "attributes", "status")}
    relation.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    relation.deleted_by = operator
    _audit(db, "DELETE", "relationship", relation.id, before, None, operator, ip, agent)
    db.commit()
