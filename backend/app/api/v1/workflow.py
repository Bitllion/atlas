"""HTTP API for workflow definitions, instances, and approval tasks."""

from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.core.security import require_permission
from app.database.session import get_db
from app.models import User, WorkflowDefinition, WorkflowInstance, WorkflowTask
from app.schemas.workflow import WorkflowDefinitionCreate, WorkflowInstanceStart, WorkflowTaskAction
from app.services import workflow as service


router = APIRouter(prefix="/workflow", tags=["workflow"])


def definition_out(item: WorkflowDefinition) -> dict:
    return {
        "id": item.id, "name": item.name, "code": item.code,
        "description": item.description, "definition": item.definition,
        "version": item.version, "is_active": item.is_active,
        "created_by": item.created_by, "created_at": item.created_at, "updated_at": item.updated_at,
    }


def task_out(item: WorkflowTask) -> dict:
    return {
        "id": item.id, "instance_id": item.instance_id, "node_id": item.node_id,
        "assignee_id": item.assignee_id, "status": item.status, "comment": item.comment,
        "actioned_by": item.actioned_by, "actioned_at": item.actioned_at,
        "created_at": item.created_at, "updated_at": item.updated_at,
    }


def instance_out(item: WorkflowInstance) -> dict:
    return {
        "id": item.id, "definition_id": item.definition_id,
        "entity_type": item.entity_type, "entity_id": item.entity_id,
        "business_key": item.business_key, "current_node_id": item.current_node_id,
        "status": item.status, "started_by": item.started_by,
        "started_at": item.started_at, "completed_at": item.completed_at,
        "version": item.version, "created_at": item.created_at, "updated_at": item.updated_at,
    }


@router.post("/definitions", status_code=status.HTTP_201_CREATED)
def create_definition(payload: WorkflowDefinitionCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("admin.manage"))):
    conflict = db.scalar(select(WorkflowDefinition.id).where((WorkflowDefinition.name == payload.name) | (WorkflowDefinition.code == payload.code)))
    if conflict:
        raise ServiceError(409, "WorkflowDefinitionConflict", "工作流名称或编码已存在")
    item = WorkflowDefinition(**payload.model_dump(), created_by=user.id)
    # Validate topology now so invalid definitions never become active records.
    db.add(item)
    db.flush()
    service.validate_topology(item)
    db.commit()
    db.refresh(item)
    return definition_out(item)


@router.get("/definitions")
def list_definitions(db: Session = Depends(get_db), _: User = Depends(require_permission("workflow.read"))):
    items = db.scalars(select(WorkflowDefinition).where(WorkflowDefinition.deleted_at.is_(None)).order_by(WorkflowDefinition.created_at.desc())).all()
    return {"items": [definition_out(item) for item in items]}


@router.post("/instances", status_code=status.HTTP_201_CREATED)
def start_instance(payload: WorkflowInstanceStart, db: Session = Depends(get_db), user: User = Depends(require_permission("workflow.write"))):
    return instance_out(service.start_workflow(db, payload.definition_code, payload.entity_type, payload.entity_id, payload.business_key, user.id))


@router.get("/tasks/my")
def my_tasks(db: Session = Depends(get_db), user: User = Depends(require_permission("workflow.read"))):
    return {"items": [task_out(item) for item in service.list_my_tasks(db, user.id)]}


@router.post("/tasks/{task_id}/approve")
def approve(task_id: UUID, payload: WorkflowTaskAction = Body(default=WorkflowTaskAction()), db: Session = Depends(get_db), user: User = Depends(require_permission("workflow.write"))):
    return instance_out(service.approve_task(db, task_id, user.id, payload.comment))


@router.post("/tasks/{task_id}/reject")
def reject(task_id: UUID, payload: WorkflowTaskAction = Body(default=WorkflowTaskAction()), db: Session = Depends(get_db), user: User = Depends(require_permission("workflow.write"))):
    return instance_out(service.reject_task(db, task_id, user.id, payload.comment))


@router.get("/instances/{instance_id}")
def instance_detail(instance_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("workflow.read"))):
    item = db.scalar(select(WorkflowInstance).where(WorkflowInstance.id == instance_id, WorkflowInstance.deleted_at.is_(None)))
    if item is None:
        raise ServiceError(404, "WorkflowInstanceNotFound", "工作流实例不存在")
    tasks = db.scalars(select(WorkflowTask).where(WorkflowTask.instance_id == item.id, WorkflowTask.deleted_at.is_(None)).order_by(WorkflowTask.created_at.asc(), WorkflowTask.id.asc())).all()
    result = instance_out(item)
    result["tasks"] = [task_out(task) for task in tasks]
    return result
