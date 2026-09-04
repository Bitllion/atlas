"""Dashboard aggregates and cross-domain global search."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, literal, or_, select, union_all
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import require_permission
from app.models import Asset, InfrastructureObject, KnowledgeArticle, ObjectType, Organization, WorkOrder

router = APIRouter(tags=["dashboard", "search"])

# TODO(resource-scope): dashboard aggregates span objects, assets, and work orders;
# apply organization scope after cross-domain work-order ownership is defined.

OPEN_STATUSES = ("CREATED", "ASSIGNED", "PROCESSING", "WAITING", "SUSPENDED", "REOPENED")


def _distribution(db: Session, statement, key: str) -> list[dict]:
    return [{key: value if value is not None else "UNASSIGNED", "count": count} for value, count in db.execute(statement).all()]


def _operations_summary(db: Session) -> dict:
    active = WorkOrder.deleted_at.is_(None)
    total = db.scalar(select(func.count()).select_from(WorkOrder).where(active)) or 0
    open_count = db.scalar(select(func.count()).select_from(WorkOrder).where(active, WorkOrder.status.in_(OPEN_STATUSES))) or 0
    month_start = func.date_trunc("month", func.now())
    new_this_month = db.scalar(select(func.count()).select_from(WorkOrder).where(active, WorkOrder.created_at >= month_start)) or 0
    resolved = db.scalar(select(func.count()).select_from(WorkOrder).where(active, WorkOrder.resolved_at.is_not(None))) or 0
    average = db.scalar(select(func.avg(func.extract("epoch", WorkOrder.resolved_at - WorkOrder.created_at)) / 3600).where(active, WorkOrder.resolved_at.is_not(None)))
    return {
        "total": total,
        "open": open_count,
        "new_this_month": new_this_month,
        "resolved": resolved,
        "average_repair_hours": round(float(average), 2) if average is not None else 0.0,
    }


@router.get("/dashboard/overview", dependencies=[Depends(require_permission("dashboard.read"))])
def dashboard_overview(db: Session = Depends(get_db)):
    object_distribution = _distribution(
        db,
        select(ObjectType.name, func.count(InfrastructureObject.id)).join(InfrastructureObject, InfrastructureObject.object_type_id == ObjectType.id).where(InfrastructureObject.deleted_at.is_(None), ObjectType.deleted_at.is_(None)).group_by(ObjectType.name).order_by(ObjectType.name),
        "type",
    )
    asset_distribution = _distribution(
        db, select(Asset.lifecycle_status, func.count()).where(Asset.deleted_at.is_(None)).group_by(Asset.lifecycle_status).order_by(Asset.lifecycle_status), "status"
    )
    return {
        "devices": {"total": sum(item["count"] for item in object_distribution), "by_type": object_distribution},
        "assets": {"total": sum(item["count"] for item in asset_distribution), "by_status": asset_distribution},
        "work_orders": _operations_summary(db),
    }


@router.get("/dashboard/assets", dependencies=[Depends(require_permission("dashboard.read"))])
def dashboard_assets(db: Session = Depends(get_db)):
    active = Asset.deleted_at.is_(None)
    by_status = _distribution(db, select(Asset.lifecycle_status, func.count()).where(active).group_by(Asset.lifecycle_status).order_by(Asset.lifecycle_status), "status")
    by_type = _distribution(
        db,
        select(ObjectType.name, func.count(Asset.id)).join(InfrastructureObject, Asset.object_id == InfrastructureObject.id).join(ObjectType, InfrastructureObject.object_type_id == ObjectType.id).where(active, InfrastructureObject.deleted_at.is_(None), ObjectType.deleted_at.is_(None)).group_by(ObjectType.name).order_by(ObjectType.name),
        "type",
    )
    by_org = _distribution(
        db,
        select(Organization.name, func.count(Asset.id)).outerjoin(Organization, Asset.owner_org_id == Organization.id).where(active).group_by(Organization.name).order_by(Organization.name),
        "organization",
    )
    return {"total": sum(item["count"] for item in by_status), "by_status": by_status, "by_type": by_type, "by_organization": by_org}


@router.get("/dashboard/operations", dependencies=[Depends(require_permission("dashboard.read"))])
def dashboard_operations(db: Session = Depends(get_db)):
    active = WorkOrder.deleted_at.is_(None)
    result = _operations_summary(db)
    result["by_status"] = _distribution(db, select(WorkOrder.status, func.count()).where(active).group_by(WorkOrder.status).order_by(WorkOrder.status), "status")
    result["by_priority"] = _distribution(db, select(WorkOrder.priority, func.count()).where(active).group_by(WorkOrder.priority).order_by(WorkOrder.priority), "priority")
    return result


@router.get("/search", dependencies=[Depends(require_permission("search.read"))])
def global_search(q: str = Query(min_length=1), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    pattern = f"%{q}%"
    objects = select(
        literal("object").label("resource_type"), InfrastructureObject.id.label("id"), InfrastructureObject.name.label("name"),
        func.concat_ws(" · ", InfrastructureObject.serial_number, InfrastructureObject.manufacturer, InfrastructureObject.model, InfrastructureObject.firmware_version).label("summary"),
    ).where(InfrastructureObject.deleted_at.is_(None), or_(InfrastructureObject.name.ilike(pattern), InfrastructureObject.serial_number.ilike(pattern), InfrastructureObject.model.ilike(pattern), InfrastructureObject.manufacturer.ilike(pattern), InfrastructureObject.firmware_version.ilike(pattern)))
    assets = select(literal("asset"), Asset.id, Asset.asset_number, func.concat("状态: ", Asset.lifecycle_status)).where(Asset.deleted_at.is_(None), Asset.asset_number.ilike(pattern))
    work_orders = select(literal("work_order"), WorkOrder.id, WorkOrder.title, func.concat(WorkOrder.work_order_number, " · ", WorkOrder.status)).where(WorkOrder.deleted_at.is_(None), or_(WorkOrder.work_order_number.ilike(pattern), WorkOrder.title.ilike(pattern)))
    articles = select(literal("knowledge_article"), KnowledgeArticle.id, KnowledgeArticle.title, func.concat(KnowledgeArticle.type, " · ", KnowledgeArticle.status)).where(KnowledgeArticle.deleted_at.is_(None), KnowledgeArticle.is_latest.is_(True), KnowledgeArticle.title.ilike(pattern))
    combined = union_all(objects, assets, work_orders, articles).subquery()
    total = db.scalar(select(func.count()).select_from(combined)) or 0
    rows = db.execute(select(combined).order_by(combined.c.resource_type, combined.c.name).offset((page - 1) * page_size).limit(page_size)).mappings().all()
    return {"query": q, "total": total, "page": page, "page_size": page_size, "items": [dict(row) for row in rows]}
