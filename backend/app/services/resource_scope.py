"""Reusable organization resource-scope predicates for read queries."""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Permission, Role, RolePermission, User, UserRole


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
