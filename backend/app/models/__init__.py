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
from app.models.knowledge import ArticleAttachment, KnowledgeArticle, KnowledgeRelation
from app.models.notification import Notification
from app.models.permission import Organization, Permission, Role, RolePermission, User, UserRole
from app.models.operations import FaultRecord, RepairRecord, ReplacementEvent, WorkOrder
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowTask

_import_models = import_module("app.models.import")
ImportError = _import_models.ImportError
ImportJob = _import_models.ImportJob

__all__ = [
    "AuditLog",
    "Asset",
    "ArticleAttachment",
    "Base",
    "IdempotencyKey",
    "Deployment",
    "InfrastructureObject",
    "ImportError",
    "ImportJob",
    "InventoryLocation",
    "InventoryRecord",
    "KnowledgeArticle",
    "KnowledgeRelation",
    "Notification",
    "FaultRecord",
    "ObjectHistory",
    "ObjectRelationship",
    "ObjectSpec",
    "ObjectType",
    "Organization",
    "Permission",
    "PurchaseOrder",
    "PurchaseRequest",
    "RepairRecord",
    "ReplacementEvent",
    "RelationshipType",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
    "WorkOrder",
    "WorkflowDefinition",
    "WorkflowInstance",
    "WorkflowTask",
]
