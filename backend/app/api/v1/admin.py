"""Administrative APIs for users, organizations, and inventory locations."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.core.security import require_current_user
from app.database.session import get_db
from app.models import AuditLog, InventoryLocation, Organization, User

router = APIRouter(tags=["admin"])


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    email: str = Field(min_length=1, max_length=255)
    password_hash: str | None = Field(default=None, max_length=255)
    organization_id: UUID


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    organization_id: UUID | None = None
    is_active: bool | None = None


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    org_type: Literal["INTERNAL", "CUSTOMER", "VENDOR"]
    contact: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=50)
    address: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


def _json_value(value: Any) -> Any:
    if isinstance(value, (UUID, datetime)):
        return str(value)
    return value


def _audit(
    db: Session,
    request: Request,
    user: User,
    action: str,
    resource_type: str,
    resource_id: UUID,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_data=before,
            after_data=after,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )


def _organization(db: Session, organization_id: UUID) -> Organization:
    organization = db.scalar(
        select(Organization).where(
            Organization.id == organization_id, Organization.deleted_at.is_(None)
        )
    )
    if organization is None:
        raise ServiceError(404, "OrganizationNotFound", "组织不存在")
    return organization


def _user(db: Session, user_id: UUID) -> User:
    item = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if item is None:
        raise ServiceError(404, "UserNotFound", "用户不存在")
    return item


def _organization_out(item: Organization) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "org_type": item.org_type,
        "contact": item.contact_email,
        "contact_email": item.contact_email,
        "contact_phone": item.contact_phone,
        "address": item.address,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _user_out(item: User, organization_name: str | None) -> dict[str, Any]:
    return {
        "id": item.id,
        "username": item.username,
        "full_name": item.full_name,
        "email": item.email,
        "organization_id": item.organization_id,
        "organization_name": organization_name,
        "is_active": item.is_active,
        "last_login_at": item.last_login_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _snapshot(item: User | Organization) -> dict[str, Any]:
    fields = (
        ("id", "username", "full_name", "email", "organization_id", "is_active")
        if isinstance(item, User)
        else ("id", "name", "org_type", "contact_email", "contact_phone", "address", "is_active")
    )
    return {field: _json_value(getattr(item, field)) for field in fields}


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    operator: User = Depends(require_current_user),
):
    organization = _organization(db, payload.organization_id)
    if db.scalar(select(User.id).where(User.username == payload.username)) is not None:
        raise ServiceError(409, "UsernameConflict", "用户名已存在")
    item = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=payload.password_hash or "PASSWORD_NOT_SET",
        organization_id=payload.organization_id,
    )
    db.add(item)
    try:
        db.flush()
        _audit(db, request, operator, "CREATE", "USER", item.id, None, _snapshot(item))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceError(409, "UserConflict", "用户名或邮箱已存在") from exc
    db.refresh(item)
    return _user_out(item, organization.name)


@router.get("/users")
def list_users(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _authenticated_user: User = Depends(require_current_user),
):
    filters = [User.deleted_at.is_(None)]
    if search:
        pattern = f"%{search}%"
        filters.append(or_(User.username.ilike(pattern), User.full_name.ilike(pattern)))
    total = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    rows = db.execute(
        select(User, Organization.name)
        .join(Organization, Organization.id == User.organization_id)
        .where(*filters)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_user_out(item, organization_name) for item, organization_name in rows],
    }


@router.get("/users/{user_id}")
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _authenticated_user: User = Depends(require_current_user),
):
    item = _user(db, user_id)
    organization_name = db.scalar(select(Organization.name).where(Organization.id == item.organization_id))
    return _user_out(item, organization_name)


@router.put("/users/{user_id}")
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    operator: User = Depends(require_current_user),
):
    item = _user(db, user_id)
    before = _snapshot(item)
    values = payload.model_dump(exclude_unset=True)
    if "organization_id" in values:
        if values["organization_id"] is None:
            raise ServiceError(422, "InvalidOrganization", "organization_id 不能为空")
        _organization(db, values["organization_id"])
    for field, value in values.items():
        setattr(item, field, value)
    item.updated_at = func.now()
    try:
        db.flush()
        _audit(db, request, operator, "UPDATE", "USER", item.id, before, _snapshot(item))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceError(409, "UserConflict", "邮箱已存在") from exc
    db.refresh(item)
    organization_name = db.scalar(select(Organization.name).where(Organization.id == item.organization_id))
    return _user_out(item, organization_name)


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    operator: User = Depends(require_current_user),
):
    values = payload.model_dump(exclude={"contact"})
    values["contact_email"] = payload.contact_email or payload.contact
    item = Organization(**values)
    db.add(item)
    try:
        db.flush()
        _audit(db, request, operator, "CREATE", "ORGANIZATION", item.id, None, _snapshot(item))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceError(409, "OrganizationConflict", "组织名称已存在") from exc
    db.refresh(item)
    return _organization_out(item)


@router.get("/organizations")
def list_organizations(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _authenticated_user: User = Depends(require_current_user),
):
    filters = [Organization.deleted_at.is_(None)]
    if search:
        filters.append(Organization.name.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(Organization).where(*filters)) or 0
    items = db.scalars(
        select(Organization)
        .where(*filters)
        .order_by(Organization.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [_organization_out(item) for item in items]}


@router.get("/organizations/{organization_id}")
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _authenticated_user: User = Depends(require_current_user),
):
    return _organization_out(_organization(db, organization_id))


@router.put("/organizations/{organization_id}")
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    operator: User = Depends(require_current_user),
):
    item = _organization(db, organization_id)
    before = _snapshot(item)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = func.now()
    try:
        db.flush()
        _audit(db, request, operator, "UPDATE", "ORGANIZATION", item.id, before, _snapshot(item))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ServiceError(409, "OrganizationConflict", "组织名称已存在") from exc
    db.refresh(item)
    return _organization_out(item)


@router.get("/inventory-locations")
def list_inventory_locations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _authenticated_user: User = Depends(require_current_user),
):
    active = InventoryLocation.deleted_at.is_(None)
    total = db.scalar(select(func.count()).select_from(InventoryLocation).where(active)) or 0
    items = db.scalars(
        select(InventoryLocation)
        .where(active)
        .order_by(InventoryLocation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    fields = ("id", "location_code", "name", "warehouse", "shelf", "description", "organization_id", "created_at", "updated_at")
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [{field: getattr(item, field) for field in fields} for item in items],
    }
