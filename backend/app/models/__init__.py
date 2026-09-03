"""Atlas SQLAlchemy model registry."""

from importlib import import_module

from app.models.base import Base
from app.models.asset import (
    Asset,
    Deployment,
    InventoryLocation,
    InventoryRecord,
    PurchaseOrder,
    PurchaseRequest,
)
from app.models.core import (
    InfrastructureObject,
    ObjectHistory,
    ObjectRelationship,
    ObjectSpec,
    ObjectType,
    RelationshipType,
)
from app.models.governance import AuditLog, IdempotencyKey
from app.models.permission import Organization, Permission, Role, RolePermission, User, UserRole

_import_models = import_module("app.models.import")
ImportError = _import_models.ImportError
ImportJob = _import_models.ImportJob

__all__ = [
    "AuditLog",
    "Asset",
    "Base",
    "IdempotencyKey",
    "Deployment",
    "InfrastructureObject",
    "ImportError",
    "ImportJob",
    "InventoryLocation",
    "InventoryRecord",
    "ObjectHistory",
    "ObjectRelationship",
    "ObjectSpec",
    "ObjectType",
    "Organization",
    "Permission",
    "PurchaseOrder",
    "PurchaseRequest",
    "RelationshipType",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
