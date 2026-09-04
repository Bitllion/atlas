"""Reusable organization resource-scope rules for reads and writes."""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Permission, Role, RolePermission, User, UserRole
from app.core.exceptions import ServiceError


def has_global_resource_access(db: Session, user: User) -> bool:
    """Admins and users granted admin.manage are not organization-scoped."""
    return db.scalar(
        select(UserRole.id)
        .join(Role, Role.id == UserRole.role_id)
        .outerjoin(RolePermission, RolePermission.role_id == Role.id)
        .outerjoin(Permission, Permission.id == RolePermission.permission_id)
        .where(
            UserRole.user_id == user.id,
            UserRole.deleted_at.is_(None),
            Role.deleted_at.is_(None),
            or_(
                Role.name == "admin",
                and_(
                    RolePermission.deleted_at.is_(None),
                    Permission.deleted_at.is_(None),
                    Permission.name == "admin.manage",
                ),
            ),
        )
        .limit(1)
    ) is not None


def organization_scope(model, organization_id):
    """Limit a resource to its owner/operator organization plus shared data."""
    shared = and_(model.owner_org_id.is_(None), model.operator_org_id.is_(None))
    if organization_id is None:
        return shared
    return or_(model.owner_org_id == organization_id, model.operator_org_id == organization_id, shared)


def require_organization_write_access(db: Session, user: User, resource) -> None:
    """Reject writes outside the user's owner/operator organization scope."""
    if has_global_resource_access(db, user):
        return
    shared = resource.owner_org_id is None and resource.operator_org_id is None
    if not shared and user.organization_id not in (resource.owner_org_id, resource.operator_org_id):
        raise ServiceError(403, "Forbidden", "无权修改其他组织的资源")


def creation_organizations(
    db: Session,
    user: User,
    owner_org_id,
    operator_org_id,
) -> tuple:
    """Validate and default owner/operator organizations for a new resource."""
    if has_global_resource_access(db, user):
        return owner_org_id, operator_org_id
    organization_id = user.organization_id
    if owner_org_id not in (None, organization_id) or operator_org_id not in (None, organization_id):
        raise ServiceError(403, "Forbidden", "不能为其他组织创建资源")
    return organization_id, organization_id
