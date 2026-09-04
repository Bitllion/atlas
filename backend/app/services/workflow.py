"""Transactional sequential-approval workflow engine."""

from collections.abc import Callable
from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models import Role, User, UserRole, WorkflowDefinition, WorkflowInstance, WorkflowTask


logger = logging.getLogger(__name__)
WorkflowCallback = Callable[[Session, WorkflowInstance], None]
_callbacks: dict[str, WorkflowCallback] = {}


def register_workflow_callback(entity_type: str, callback: WorkflowCallback) -> None:
    """Register a domain callback without coupling the engine to that domain."""
    _callbacks[entity_type.upper()] = callback


def unregister_workflow_callback(entity_type: str) -> None:
    _callbacks.pop(entity_type.upper(), None)


# Short aliases are convenient for domain service initialization.
register_callback = register_workflow_callback
unregister_callback = unregister_workflow_callback


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _node_map(definition: WorkflowDefinition) -> dict[str, dict]:
    return {node["id"]: node for node in definition.definition["nodes"]}


def _edge_ends(edge: dict) -> tuple[str | None, str | None]:
    return edge.get("source", edge.get("from")), edge.get("target", edge.get("to"))


def _first_node(definition: WorkflowDefinition) -> dict:
    nodes = definition.definition.get("nodes", [])
    incoming = {_edge_ends(edge)[1] for edge in definition.definition.get("edges", [])}
    starts = [node for node in nodes if node["id"] not in incoming]
    if len(starts) != 1:
        raise ServiceError(400, "InvalidWorkflowDefinition", "工作流必须有且仅有一个起始节点")
    return starts[0]


def _next_node(definition: WorkflowDefinition, node_id: str) -> dict | None:
    targets = [target for edge in definition.definition.get("edges", []) for source, target in [_edge_ends(edge)] if source == node_id]
    if len(targets) > 1:
        raise ServiceError(400, "UnsupportedWorkflowBranch", "当前版本仅支持顺序审批链")
    if not targets:
        return None
    node = _node_map(definition).get(targets[0])
    if node is None:
        raise ServiceError(400, "InvalidWorkflowDefinition", "工作流边引用了不存在的节点")
    return node


def validate_topology(definition: WorkflowDefinition) -> None:
    """Ensure the MVP graph is one connected, acyclic sequential chain."""
    node = _first_node(definition)
    visited: set[str] = set()
    while node is not None:
        if node["id"] in visited:
            raise ServiceError(400, "InvalidWorkflowDefinition", "工作流不可包含循环")
        visited.add(node["id"])
        if node.get("type") in {"end", "terminal"} and _next_node(definition, node["id"]) is not None:
            raise ServiceError(400, "InvalidWorkflowDefinition", "终点节点不可再连接后续节点")
        node = _next_node(definition, node["id"])
    if len(visited) != len(definition.definition["nodes"]):
        raise ServiceError(400, "InvalidWorkflowDefinition", "工作流必须是连通的顺序审批链")


def _assignees(db: Session, node: dict) -> list[UUID]:
    user_ids: set[UUID] = set()
    raw_user_id = node.get("assignee_user_id", node.get("user_id"))
    if raw_user_id:
        try:
            requested = UUID(str(raw_user_id))
        except ValueError as exc:
            raise ServiceError(400, "InvalidWorkflowAssignee", "审批节点 user_id 格式无效") from exc
        exists = db.scalar(select(User.id).where(User.id == requested, User.is_active.is_(True), User.deleted_at.is_(None)))
        if exists:
            user_ids.add(exists)
    role_name = node.get("assignee_role")
    if role_name:
        users = db.scalars(
            select(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                Role.name == role_name, Role.deleted_at.is_(None),
                UserRole.deleted_at.is_(None), User.is_active.is_(True), User.deleted_at.is_(None),
            )
        )
        user_ids.update(users)
    if not user_ids:
        raise ServiceError(400, "WorkflowAssigneeNotFound", f"节点 {node['id']} 没有可用审批人")
    return sorted(user_ids, key=str)


def _create_node_tasks(db: Session, instance: WorkflowInstance, node: dict) -> None:
    if node.get("type") != "approval":
        raise ServiceError(400, "UnsupportedWorkflowNode", "当前版本仅支持审批节点和终点节点")
    instance.current_node_id = node["id"]
    for assignee_id in _assignees(db, node):
        db.add(WorkflowTask(instance_id=instance.id, node_id=node["id"], assignee_id=assignee_id))


def _finish(db: Session, instance: WorkflowInstance, status: str) -> None:
    instance.status = status
    instance.current_node_id = None
    instance.completed_at = _now()
    instance.version += 1
    callback = _callbacks.get(instance.entity_type.upper())
    if callback:
        callback(db, instance)
    elif instance.entity_type.upper() == "PURCHASE_REQUEST":
        logger.info("PURCHASE_REQUEST workflow %s ended with no business callback registered", instance.id)


def start_workflow(db: Session, definition_code: str, entity_type: str, entity_id: UUID, business_key: str | None, initiator: UUID) -> WorkflowInstance:
    definition = db.scalar(select(WorkflowDefinition).where(WorkflowDefinition.code == definition_code, WorkflowDefinition.is_active.is_(True), WorkflowDefinition.deleted_at.is_(None)))
    if definition is None:
        raise ServiceError(404, "WorkflowDefinitionNotFound", "工作流定义不存在或未启用")
    validate_topology(definition)
    first = _first_node(definition)
    instance = WorkflowInstance(definition_id=definition.id, entity_type=entity_type.upper(), entity_id=entity_id, business_key=business_key, started_by=initiator)
    db.add(instance)
    db.flush()
    if first.get("type") in {"end", "terminal"}:
        _finish(db, instance, "COMPLETED")
    else:
        _create_node_tasks(db, instance, first)
    db.commit()
    db.refresh(instance)
    return instance


def _pending_task(db: Session, task_id: UUID, actor: UUID) -> tuple[WorkflowTask, WorkflowInstance, WorkflowDefinition]:
    task = db.scalar(select(WorkflowTask).where(WorkflowTask.id == task_id, WorkflowTask.deleted_at.is_(None)).with_for_update())
    if task is None:
        raise ServiceError(404, "WorkflowTaskNotFound", "工作流任务不存在")
    if task.status != "PENDING":
        raise ServiceError(409, "WorkflowTaskAlreadyActioned", "工作流任务已处理")
    if task.assignee_id != actor:
        raise ServiceError(403, "WorkflowTaskNotAssigned", "该任务未分派给当前用户")
    instance = db.scalar(select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id, WorkflowInstance.deleted_at.is_(None)).with_for_update())
    if instance is None or instance.status != "RUNNING" or instance.current_node_id != task.node_id:
        raise ServiceError(409, "WorkflowInstanceNotRunning", "工作流实例当前不可处理")
    definition = db.get(WorkflowDefinition, instance.definition_id)
    if definition is None:
        raise ServiceError(500, "WorkflowDefinitionMissing", "工作流定义数据缺失")
    return task, instance, definition


def approve_task(db: Session, task_id: UUID, actor: UUID, comment: str | None = None) -> WorkflowInstance:
    task, instance, definition = _pending_task(db, task_id, actor)
    now = _now()
    task.status, task.comment, task.actioned_by, task.actioned_at = "APPROVED", comment, actor, now
    siblings = db.scalars(select(WorkflowTask).where(WorkflowTask.instance_id == instance.id, WorkflowTask.node_id == task.node_id, WorkflowTask.status == "PENDING", WorkflowTask.id != task.id, WorkflowTask.deleted_at.is_(None)).with_for_update()).all()
    for sibling in siblings:
        sibling.status, sibling.actioned_at = "SKIPPED", now
    next_node = _next_node(definition, task.node_id)
    if next_node is None or next_node.get("type") in {"end", "terminal"}:
        _finish(db, instance, "COMPLETED")
    else:
        instance.version += 1
        _create_node_tasks(db, instance, next_node)
    db.commit()
    db.refresh(instance)
    return instance


def reject_task(db: Session, task_id: UUID, actor: UUID, comment: str | None = None) -> WorkflowInstance:
    task, instance, _ = _pending_task(db, task_id, actor)
    now = _now()
    task.status, task.comment, task.actioned_by, task.actioned_at = "REJECTED", comment, actor, now
    siblings = db.scalars(select(WorkflowTask).where(WorkflowTask.instance_id == instance.id, WorkflowTask.node_id == task.node_id, WorkflowTask.status == "PENDING", WorkflowTask.id != task.id, WorkflowTask.deleted_at.is_(None)).with_for_update()).all()
    for sibling in siblings:
        sibling.status, sibling.actioned_at = "SKIPPED", now
    _finish(db, instance, "TERMINATED")
    db.commit()
    db.refresh(instance)
    return instance


def list_my_tasks(db: Session, actor: UUID) -> list[WorkflowTask]:
    return list(db.scalars(select(WorkflowTask).where(WorkflowTask.assignee_id == actor, WorkflowTask.status == "PENDING", WorkflowTask.deleted_at.is_(None)).order_by(WorkflowTask.created_at.asc())))
