"""HTTP routes for Phase 3a asset lifecycle management."""

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import actor_id, get_current_user_optional
from app.models import Asset, Deployment, PurchaseRequest, User
from app.schemas.assets import (AssetReceive, DeployAsset, InventoryLocationCreate,
                                PurchaseDecision, PurchaseRejection,
                                PurchaseRequestCreate, StockAsset, InventoryReceive,
                                DeploymentCreate)
from app.services import assets as service

router = APIRouter()


@router.post("/purchase-requests", status_code=status.HTTP_201_CREATED, tags=["assets"])
def create_purchase_request(payload: PurchaseRequestCreate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.purchase_out(service.create_purchase(db, payload, actor_id(user)))


@router.get("/purchase-requests", tags=["assets"])
def list_purchase_requests(db: Session = Depends(get_db)):
    return {"items": [service.purchase_out(item) for item in db.scalars(select(PurchaseRequest).order_by(PurchaseRequest.created_at.desc()))]}


@router.post("/purchase-requests/{request_id}/approve", tags=["assets"])
def approve_purchase_request(request_id: UUID, payload: PurchaseDecision, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.purchase_out(service.decide_purchase(db, request_id, payload, True, actor_id(user)))


@router.post("/purchase-requests/{request_id}/reject", tags=["assets"])
def reject_purchase_request(request_id: UUID, payload: PurchaseRejection, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.purchase_out(service.decide_purchase(db, request_id, payload, False, actor_id(user)))


@router.post("/inventory-locations", status_code=status.HTTP_201_CREATED, tags=["assets"])
def create_inventory_location(payload: InventoryLocationCreate, db: Session = Depends(get_db)):
    return service.create_inventory_location(db, payload)


@router.post("/assets", status_code=status.HTTP_201_CREATED, tags=["assets"])
def receive_assets(payload: AssetReceive | list[AssetReceive] = Body(...), db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    many = isinstance(payload, list)
    items = payload if many else [payload]
    result = [service.asset_out(db, asset) for asset in service.receive_assets(db, items, actor_id(user))]
    return result if many else result[0]


@router.put("/assets/{asset_id}/stock", tags=["assets"])
def stock_asset(asset_id: UUID, payload: StockAsset, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.asset_out(db, service.stock_asset(db, asset_id, payload, actor_id(user)))


@router.post("/inventory/receive", tags=["assets"])
def receive_into_inventory(payload: InventoryReceive, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.asset_out(db, service.stock_asset(db, payload.asset_id, StockAsset(**payload.model_dump(exclude={"asset_id"})), actor_id(user)))


@router.put("/assets/{asset_id}/deploy", tags=["assets"])
def deploy_asset(asset_id: UUID, payload: DeployAsset, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.asset_out(db, service.deploy_asset(db, asset_id, payload, actor_id(user)))


@router.post("/deployments", tags=["assets"])
def create_deployment(payload: DeploymentCreate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.asset_out(db, service.deploy_asset(db, payload.asset_id, DeployAsset(**payload.model_dump(exclude={"asset_id"})), actor_id(user)))


@router.get("/deployments", tags=["assets"])
def list_deployments(asset_id: UUID | None = None, location_id: UUID | None = None, db: Session = Depends(get_db)):
    query = select(Deployment)
    if asset_id: query = query.where(Deployment.asset_id == asset_id)
    if location_id: query = query.where(Deployment.location_id == location_id)
    items = db.scalars(query.order_by(Deployment.created_at.desc())).all()
    fields = ("id", "asset_id", "object_id", "location_id", "deployment_type", "status", "acceptance_status", "deployed_by", "deployed_at", "notes", "created_at")
    return {"items": [{field: getattr(item, field) for field in fields} for item in items]}


@router.get("/assets", tags=["assets"])
def list_assets(lifecycle_status: str | None = Query(default=None, alias="status"), organization_id: UUID | None = None, location_id: UUID | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    total, items = service.list_assets(db, lifecycle_status, organization_id, location_id, page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [service.asset_out(db, item) for item in items]}


@router.get("/assets/{asset_id}", tags=["assets"])
def get_asset(asset_id: UUID, db: Session = Depends(get_db)):
    asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.deleted_at.is_(None)))
    if asset is None:
        from app.core.exceptions import ServiceError
        raise ServiceError(404, "AssetNotFound", "资产不存在")
    return service.asset_out(db, asset, detail=True)


@router.get("/assets/{asset_id}/lifecycle", tags=["assets"])
def get_asset_lifecycle(asset_id: UUID, db: Session = Depends(get_db)):
    return {"asset_id": asset_id, "items": service.lifecycle(db, asset_id)}
