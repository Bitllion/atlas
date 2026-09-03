"""Organization and role-based access-control persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin


class Organization(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("org_type IN ('INTERNAL', 'CUSTOMER', 'VENDOR')", name="ck_organizations_org_type"),
        Index("idx_organizations_type", "org_type", "is_active"),
        Index("idx_organizations_parent", "parent_org_id"),
        Index("idx_organizations_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(255), unique=True)
    org_type: Mapped[str] = mapped_column(String(50))
    parent_org_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class User(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_org", "organization_id", "is_active"),
        Index(
            "idx_users_email",
            "email",
            postgresql_where=text("is_active = TRUE AND deleted_at IS NULL"),
        ),
        Index("idx_users_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    last_login_at: Mapped[datetime | None]


class Role(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        Index("idx_roles_organization", "organization_id"),
        Index("idx_roles_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))


class Permission(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (
        Index("idx_permissions_resource", "resource_type", "action"),
        Index("idx_permissions_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)


class UserRole(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("idx_user_roles_user", "user_id"),
        Index("idx_user_roles_role", "role_id"),
        Index("idx_user_roles_granted_by", "granted_by"),
        Index("idx_user_roles_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"))
    granted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    granted_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class RolePermission(IdMixin, SoftDeleteMixin, CreatedAtMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        Index("idx_role_permissions_role", "role_id"),
        Index("idx_role_permissions_permission", "permission_id"),
        Index("idx_role_permissions_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id"))
