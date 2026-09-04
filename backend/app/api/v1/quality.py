"""Data quality center API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, literal_column, or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import require_permission
from app.models import InfrastructureObject, ObjectSpec, ObjectType, User
from app.services.resource_scope import has_global_resource_access, organization_scope

router = APIRouter(tags=["quality"])


@router.get("/quality/overview")
def quality_overview(db: Session = Depends(get_db), user: User = Depends(require_permission("quality.read"))):
    """Aggregate data quality metrics by object type."""
    filters = [InfrastructureObject.deleted_at.is_(None), ObjectType.deleted_at.is_(None)]
    if not has_global_resource_access(db, user):
        filters.append(organization_scope(InfrastructureObject, user.organization_id))

    # Build aggregation query
    query = (
        select(
            ObjectType.name.label("object_type"),
            func.count(InfrastructureObject.id).label("total"),
            func.sum(case((InfrastructureObject.serial_number.is_(None), 1), else_=0)).label("missing_serial_number"),
            func.sum(case((InfrastructureObject.manufacturer.is_(None), 1), else_=0)).label("missing_manufacturer"),
            func.sum(case((InfrastructureObject.model.is_(None), 1), else_=0)).label("missing_model"),
            func.sum(case((ObjectSpec.id.is_(None), 1), else_=0)).label("missing_spec"),
            func.sum(case((and_(ObjectSpec.id.is_not(None), ObjectSpec.data_status == "STALE"), 1), else_=0)).label("stale_spec"),
            func.sum(case((and_(ObjectSpec.id.is_not(None), ObjectSpec.data_status == "UNKNOWN"), 1), else_=0)).label("unknown_spec"),
            func.sum(case((and_(ObjectSpec.id.is_not(None), ObjectSpec.confidence == "LOW"), 1), else_=0)).label("low_confidence"),
        )
        .select_from(InfrastructureObject)
        .join(ObjectType, InfrastructureObject.object_type_id == ObjectType.id)
        .outerjoin(ObjectSpec, and_(
            ObjectSpec.object_id == InfrastructureObject.id,
            ObjectSpec.deleted_at.is_(None)
        ))
        .where(*filters)
        .group_by(ObjectType.name)
        .order_by(ObjectType.name)
    )

    rows = db.execute(query).mappings().all()

    return {
        "by_type": [
            {
                "object_type": row["object_type"],
                "total": row["total"],
                "missing_serial_number": row["missing_serial_number"],
                "missing_manufacturer": row["missing_manufacturer"],
                "missing_model": row["missing_model"],
                "missing_spec": row["missing_spec"],
                "spec_status": {
                    "stale": row["stale_spec"],
                    "unknown": row["unknown_spec"],
                },
                "low_confidence": row["low_confidence"],
            }
            for row in rows
        ]
    }


@router.get("/quality/details")
def quality_details(
    object_type: str | None = Query(None, alias="type"),
    missing: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("quality.read")),
):
    """List objects with quality issues, with optional filters."""
    filters = [InfrastructureObject.deleted_at.is_(None), ObjectType.deleted_at.is_(None)]
    if not has_global_resource_access(db, user):
        filters.append(organization_scope(InfrastructureObject, user.organization_id))

    if object_type:
        filters.append(ObjectType.name == object_type)

    # Apply missing field filter
    if missing == "serial_number":
        filters.append(InfrastructureObject.serial_number.is_(None))
    elif missing == "manufacturer":
        filters.append(InfrastructureObject.manufacturer.is_(None))
    elif missing == "model":
        filters.append(InfrastructureObject.model.is_(None))
    elif missing == "spec":
        # Filter to objects without specs - use left join and check for NULL
        filters.append(ObjectSpec.id.is_(None))

    # Base query
    base_query = (
        select(InfrastructureObject, ObjectType.name, ObjectSpec.data_status, ObjectSpec.confidence)
        .join(ObjectType, InfrastructureObject.object_type_id == ObjectType.id)
        .outerjoin(ObjectSpec, and_(
            ObjectSpec.object_id == InfrastructureObject.id,
            ObjectSpec.deleted_at.is_(None)
        ))
        .where(*filters)
    )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = db.scalar(count_query) or 0

    # Fetch paginated results
    items_query = base_query.order_by(InfrastructureObject.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(items_query).all()

    items = []
    for obj, type_name, data_status, confidence in rows:
        missing_fields = []
        if obj.serial_number is None:
            missing_fields.append("serial_number")
        if obj.manufacturer is None:
            missing_fields.append("manufacturer")
        if obj.model is None:
            missing_fields.append("model")
        if data_status is None:
            missing_fields.append("spec")

        items.append({
            "id": obj.id,
            "name": obj.name,
            "object_type": type_name,
            "missing_fields": missing_fields,
            "data_status": data_status,
            "confidence": confidence,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/quality/unattributed")
def quality_unattributed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("quality.read")),
):
    """List objects with no owner or operator organization."""
    filters = [
        InfrastructureObject.deleted_at.is_(None),
        ObjectType.deleted_at.is_(None),
        InfrastructureObject.owner_org_id.is_(None),
        InfrastructureObject.operator_org_id.is_(None),
    ]

    # Non-admin users can only see unattributed objects (which are effectively shared)
    if not has_global_resource_access(db, user):
        # Unattributed objects are visible to all users per organization_scope logic
        pass

    # Count total
    count_query = (
        select(func.count())
        .select_from(InfrastructureObject)
        .join(ObjectType, InfrastructureObject.object_type_id == ObjectType.id)
        .where(*filters)
    )
    total = db.scalar(count_query) or 0

    # Fetch paginated results
    items_query = (
        select(InfrastructureObject, ObjectType.name)
        .join(ObjectType, InfrastructureObject.object_type_id == ObjectType.id)
        .where(*filters)
        .order_by(InfrastructureObject.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(items_query).all()

    items = [
        {
            "id": obj.id,
            "name": obj.name,
            "object_type": type_name,
            "serial_number": obj.serial_number,
            "manufacturer": obj.manufacturer,
            "model": obj.model,
            "status": obj.status,
        }
        for obj, type_name in rows
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
