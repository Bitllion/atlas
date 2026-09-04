"""HTTP routes for the Infrastructure Core API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import actor_id, get_current_user_optional, require_permission
from app.models import ObjectHistory, ObjectRelationship, ObjectType, RelationshipType, User
from app.schemas.core import HistoryOut, ObjectCreate, ObjectDetail, ObjectOut, ObjectUpdate, RelationshipCreate, RelationshipOut
from app.services import core as service

router = APIRouter()


def context(request: Request) -> tuple[str | None, str | None]:
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


def relationship_out(item: ObjectRelationship) -> dict:
    return {
        "id": item.id,
        "source_object_id": item.source_object_id,
        "relationship_type_id": item.relation_type_id,
        "target_object_id": item.target_object_id,
        "attributes": item.attributes,
        "status": item.status,
        "confidence": item.confidence,
        "data_source": item.data_source,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.post("/objects", response_model=ObjectOut, status_code=status.HTTP_201_CREATED, tags=["objects"], dependencies=[Depends(require_permission("object.write"))])
def create_object(payload: ObjectCreate, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    body = payload.model_dump(mode="json")
    cached = service.idempotency_lookup(db, idempotency_key, "/api/v1/objects", body)
    if cached:
        return JSONResponse(status_code=cached["status"], content=cached["body"])
    ip, agent = context(request)
    actor = actor_id(user)
    result = service.create_object(db, payload, user, ip, agent)
    response_body = jsonable_encoder(ObjectOut.model_validate(result))
    service.idempotency_store(db, idempotency_key, "/api/v1/objects", body, 201, response_body, actor)
    return result


@router.get("/objects", tags=["objects"])
def list_objects(object_type_id: UUID | None = None, object_type: str | None = None, status_filter: str | None = Query(default=None, alias="status"), name: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(require_permission("object.read"))):
    if object_type and not object_type_id:
        object_type_id = db.scalar(select(ObjectType.id).where(ObjectType.name == object_type, ObjectType.deleted_at.is_(None)))
        if object_type_id is None:
            return {"total": 0, "page": page, "page_size": page_size, "items": []}
    total, items = service.list_objects(db, object_type_id, status_filter, name, page, page_size, user)
    return {"total": total, "page": page, "page_size": page_size, "items": [ObjectOut.model_validate(item) for item in items]}


@router.get("/objects/{object_id}", response_model=ObjectDetail, tags=["objects"], dependencies=[Depends(require_permission("object.read"))])
def get_object(object_id: UUID, db: Session = Depends(get_db)):
    return service.object_detail(db, object_id)


def expected_version(if_match: str | None, body_version: int | None) -> int:
    if if_match:
        value = if_match.strip().strip('"')
        if value.lower().startswith("v"):
            value = value[1:]
        try:
            return int(value)
        except ValueError as exc:
            from app.core.exceptions import ServiceError
            raise ServiceError(400, "InvalidIfMatch", "If-Match 必须是版本号") from exc
    if body_version is not None:
        return body_version
    from app.core.exceptions import ServiceError
    raise ServiceError(428, "VersionRequired", "更新对象必须提供 If-Match 或 version")


@router.put("/objects/{object_id}", response_model=ObjectOut, tags=["objects"], dependencies=[Depends(require_permission("object.write"))])
def update_object(object_id: UUID, payload: ObjectUpdate, request: Request, db: Session = Depends(get_db), if_match: str | None = Header(default=None, alias="If-Match"), user: User | None = Depends(get_current_user_optional), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    body = payload.model_dump(mode="json", exclude_unset=True)
    endpoint = f"/api/v1/objects/{object_id}"
    cached = service.idempotency_lookup(db, idempotency_key, endpoint, body)
    if cached:
        return JSONResponse(status_code=cached["status"], content=cached["body"])
    ip, agent = context(request)
    actor = actor_id(user)
    result = service.update_object(db, object_id, payload, expected_version(if_match, payload.version), user, ip, agent)
    service.idempotency_store(db, idempotency_key, endpoint, body, 200, jsonable_encoder(ObjectOut.model_validate(result)), actor)
    return result


@router.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["objects"], dependencies=[Depends(require_permission("object.write"))])
def delete_object(object_id: UUID, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> Response:
    endpoint = f"/api/v1/objects/{object_id}"
    cached = service.idempotency_lookup(db, idempotency_key, endpoint, {})
    if cached:
        return Response(status_code=cached["status"])
    ip, agent = context(request)
    actor = actor_id(user)
    service.delete_object(db, object_id, user, ip, agent)
    service.idempotency_store(db, idempotency_key, endpoint, {}, 204, None, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/objects/{object_id}/history", tags=["objects"], dependencies=[Depends(require_permission("object.read"))])
def object_history(object_id: UUID, db: Session = Depends(get_db)):
    service._active_object(db, object_id)
    items = list(db.scalars(select(ObjectHistory).where(ObjectHistory.object_id == object_id, ObjectHistory.deleted_at.is_(None)).order_by(ObjectHistory.created_at.desc())))
    return {"items": [HistoryOut.model_validate(item) for item in items]}


@router.post("/relationships", response_model=RelationshipOut, status_code=status.HTTP_201_CREATED, tags=["relationships"], dependencies=[Depends(require_permission("object.write"))])
def create_relationship(payload: RelationshipCreate, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    body = payload.model_dump(mode="json")
    cached = service.idempotency_lookup(db, idempotency_key, "/api/v1/relationships", body)
    if cached:
        return JSONResponse(status_code=cached["status"], content=cached["body"])
    ip, agent = context(request)
    actor = actor_id(user)
    result = relationship_out(service.create_relationship(db, payload, user, ip, agent))
    service.idempotency_store(db, idempotency_key, "/api/v1/relationships", body, 201, jsonable_encoder(result), actor)
    return result


@router.get("/relationships", tags=["relationships"], dependencies=[Depends(require_permission("object.read"))])
def list_relationships(source_id: UUID | None = None, target_id: UUID | None = None, relation_type: str | None = None, source_object_id: UUID | None = None, target_object_id: UUID | None = None, relationship_type_id: UUID | None = None, db: Session = Depends(get_db)):
    query = select(ObjectRelationship).where(ObjectRelationship.deleted_at.is_(None))
    source = source_id or source_object_id
    target = target_id or target_object_id
    if source:
        query = query.where(ObjectRelationship.source_object_id == source)
    if target:
        query = query.where(ObjectRelationship.target_object_id == target)
    if relationship_type_id:
        query = query.where(ObjectRelationship.relation_type_id == relationship_type_id)
    elif relation_type:
        query = query.join(RelationshipType, RelationshipType.id == ObjectRelationship.relation_type_id).where(RelationshipType.name == relation_type, RelationshipType.deleted_at.is_(None))
    items = list(db.scalars(query.order_by(ObjectRelationship.created_at.desc())))
    return {"items": [relationship_out(item) for item in items]}


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["relationships"], dependencies=[Depends(require_permission("object.write"))])
def delete_relationship(relationship_id: UUID, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> Response:
    endpoint = f"/api/v1/relationships/{relationship_id}"
    cached = service.idempotency_lookup(db, idempotency_key, endpoint, {})
    if cached:
        return Response(status_code=cached["status"])
    ip, agent = context(request)
    actor = actor_id(user)
    service.delete_relationship(db, relationship_id, user, ip, agent)
    service.idempotency_store(db, idempotency_key, endpoint, {}, 204, None, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/object-types", tags=["types"], dependencies=[Depends(require_permission("object.read"))])
def object_types(db: Session = Depends(get_db)):
    items = list(db.scalars(select(ObjectType).where(ObjectType.deleted_at.is_(None)).order_by(ObjectType.name)))
    return {"items": [{"id": item.id, "name": item.name, "display_name": item.description, "category": item.category} for item in items]}


@router.get("/relationship-types", tags=["types"], dependencies=[Depends(require_permission("object.read"))])
def relationship_types(db: Session = Depends(get_db)):
    items = list(db.scalars(select(RelationshipType).where(RelationshipType.deleted_at.is_(None)).order_by(RelationshipType.name)))
    return {"items": [{"id": item.id, "name": item.name, "display_name": item.description, "is_directed": item.is_directed} for item in items]}
