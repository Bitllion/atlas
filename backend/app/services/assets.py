"""Transactional asset lifecycle business logic."""

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models import (
    Asset, Deployment, InfrastructureObject, InventoryLocation, InventoryRecord,
    ObjectHistory, ObjectRelationship, ObjectSpec, ObjectType, Organization, PurchaseRequest,
    RelationshipType, User, WorkflowInstance, WorkflowTask,
)
from app.schemas.assets import (AssetReceive, CompleteTransfer, DeployAsset, InventoryLocationCreate,
                                PurchaseDecision, PurchaseRejection,
                                PurchaseRequestCreate, RecoverAsset, RetireAsset,
                                StockAsset, TransferAsset)
from app.services.core import _operator
from app.services.resource_scope import (creation_organizations, has_global_resource_access,
                                         organization_scope, require_organization_write_access)

ALLOWED_TRANSITIONS = {
    "REQUESTED": {"APPROVED"}, "APPROVED": {"ORDERED"},
    "ORDERED": {"PURCHASED"}, "PURCHASED": {"RECEIVED"},
    "RECEIVED": {"STOCK", "IN_TRANSIT"}, "STOCK": {"IN_TRANSIT", "TRANSFERRED", "DEPLOYED", "RETIRED"},
    "IN_TRANSIT": {"DEPLOYING", "STOCK"}, "DEPLOYING": {"DEPLOYED", "STOCK"},
    "DEPLOYED": {"ACTIVE"}, "ACTIVE": {"MAINTENANCE", "TRANSFERRED", "RETIRED"},
    "MAINTENANCE": {"ACTIVE", "RETIRED"}, "TRANSFERRED": {"STOCK", "DEPLOYING"},
    "RETIRED": {"RECOVERED"}, "RECOVERED": {"STOCK", "MAINTENANCE"},
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _request_number() -> str:
    return f"PR-{datetime.now():%Y%m%d}-{uuid4().hex[:8].upper()}"


def _required_user(db: Session, explicit: UUID | None, header_user: str | None, role: str) -> UUID:
    operator = explicit or _operator(header_user)
    if operator is None:
        raise ServiceError(422, "UserRequired", f"必须提供{role}用户 ID")
    if db.scalar(select(User.id).where(User.id == operator, User.deleted_at.is_(None), User.is_active.is_(True))) is None:
        raise ServiceError(422, "InvalidUser", f"{role}用户不存在或已停用")
    return operator


def _active_asset(db: Session, asset_id: UUID) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.deleted_at.is_(None)))
    if asset is None:
        raise ServiceError(404, "AssetNotFound", "资产不存在")
    return asset


def _require_transition(asset: Asset, target: str) -> None:
    if target not in ALLOWED_TRANSITIONS.get(asset.lifecycle_status, set()):
        raise ServiceError(409, "InvalidAssetTransition", f"资产状态 {asset.lifecycle_status} 不能转换为 {target}")


def _require_version(asset: Asset, expected: int | None) -> None:
    if expected is not None and asset.version != expected:
        raise ServiceError(409, "ConcurrentModificationError", "资源已被修改，请刷新后重试", current_version=asset.version, expected_version=expected)


def _history(db: Session, asset: Asset, old: str | None, new: str, operator: UUID | None, **extra: Any) -> None:
    db.add(ObjectHistory(
        object_id=asset.object_id, change_type="STATUS_CHANGE",
        before_data={"asset_id": str(asset.id), "lifecycle_status": old} if old else None,
        after_data={"asset_id": str(asset.id), "lifecycle_status": new, **extra},
        source="API", confidence="HIGH", operator=operator, created_at=_now(),
    ))


def purchase_out(item: PurchaseRequest) -> dict[str, Any]:
    return {key: getattr(item, key) for key in (
        "id", "request_number", "title", "object_type_id", "model", "quantity",
        "estimated_cost", "currency", "justification", "preferred_vendor", "items",
        "status", "requester_id", "approved_by", "approved_at", "rejected_by",
        "rejected_at", "rejection_reason", "workflow_instance_id", "created_at", "updated_at")}


def create_purchase(db: Session, payload: PurchaseRequestCreate, header_user: str | None) -> PurchaseRequest:
    type_ids = {row[0] for row in db.execute(select(ObjectType.id).where(ObjectType.deleted_at.is_(None)))}
    if any(item.object_type_id not in type_ids for item in payload.items):
        raise ServiceError(400, "InvalidObjectType", "采购明细包含不存在的对象类型")
    first = payload.items[0]
    estimated = payload.estimated_cost
    if estimated is None and all(i.unit_budget is not None for i in payload.items):
        estimated = sum((i.unit_budget or 0) * i.quantity for i in payload.items)
    requester = _required_user(db, payload.requester_id, header_user, "申请人")
    request = PurchaseRequest(
        request_number=_request_number(), title=payload.title,
        object_type_id=first.object_type_id, model=first.model,
        quantity=sum(item.quantity for item in payload.items), estimated_cost=estimated,
        currency=payload.currency, justification=payload.justification,
        preferred_vendor=payload.preferred_vendor,
        items=[item.model_dump(mode="json") for item in payload.items],
        status="PENDING", requester_id=requester,
    )
    db.add(request)
    db.flush()
    from app.services import workflow
    instance = workflow.start_workflow(
        db, "purchase_approval", "PURCHASE_REQUEST", request.id,
        request.request_number, requester, commit=False,
    )
    request.workflow_instance_id = instance.id
    db.commit()
    db.refresh(request)
    return request


def decide_purchase(db: Session, request_id: UUID, payload: PurchaseDecision | PurchaseRejection, approve: bool, header_user: str | None) -> PurchaseRequest:
    request = db.get(PurchaseRequest, request_id)
    if request is None:
        raise ServiceError(404, "PurchaseRequestNotFound", "采购申请不存在")
    if request.status != "PENDING":
        raise ServiceError(409, "InvalidPurchaseTransition", f"采购申请状态 {request.status} 不允许审批")
    active_workflow = db.scalar(select(WorkflowInstance.id).where(
        WorkflowInstance.entity_type == "PURCHASE_REQUEST",
        WorkflowInstance.entity_id == request.id,
        WorkflowInstance.status == "RUNNING",
        WorkflowInstance.deleted_at.is_(None),
    ))
    if active_workflow is not None:
        raise ServiceError(409, "PurchaseWorkflowActive", "采购申请已进入工作流，请通过待办任务审批")
    operator = _required_user(db, payload.approved_by if approve else payload.rejected_by, header_user, "审批人")
    if approve:
        request.status, request.approved_by, request.approved_at = "APPROVED", operator, _now()
    else:
        request.status, request.rejected_by, request.rejected_at = "REJECTED", operator, _now()
        request.rejection_reason = payload.rejection_reason
    request.updated_at = _now()
    from app.services.notification import notify
    result_label = "已批准" if approve else "被驳回"
    notification_type = "PURCHASE_APPROVED" if approve else "PURCHASE_REJECTED"
    notify(db, request.requester_id, notification_type, "采购审批结果",
           f"采购单 {request.request_number} {result_label}", "PURCHASE_REQUEST", request.id)
    db.commit()
    db.refresh(request)
    return request


def purchase_workflow(db: Session, request_id: UUID, user: User) -> tuple[PurchaseRequest, WorkflowInstance, list[WorkflowTask]]:
    query = select(PurchaseRequest).join(User, User.id == PurchaseRequest.requester_id).where(PurchaseRequest.id == request_id)
    if not has_global_resource_access(db, user):
        query = query.where(User.organization_id == user.organization_id)
    request = db.scalar(query)
    if request is None:
        raise ServiceError(404, "PurchaseRequestNotFound", "采购申请不存在")
    instance = db.scalar(select(WorkflowInstance).where(
        WorkflowInstance.entity_type == "PURCHASE_REQUEST",
        WorkflowInstance.entity_id == request.id,
        WorkflowInstance.deleted_at.is_(None),
    ).order_by(WorkflowInstance.started_at.desc()))
    if instance is None:
        raise ServiceError(404, "PurchaseWorkflowNotFound", "采购申请未关联工作流")
    tasks = list(db.scalars(select(WorkflowTask).where(
        WorkflowTask.instance_id == instance.id,
        WorkflowTask.status == "PENDING",
        WorkflowTask.deleted_at.is_(None),
    ).order_by(WorkflowTask.created_at.asc(), WorkflowTask.id.asc())))
    return request, instance, tasks


def _purchase_workflow_callback(db: Session, instance: WorkflowInstance) -> None:
    request = db.scalar(select(PurchaseRequest).where(PurchaseRequest.id == instance.entity_id).with_for_update())
    if request is None or request.status != "PENDING":
        return
    final_task = db.scalar(select(WorkflowTask).where(
        WorkflowTask.instance_id == instance.id,
        WorkflowTask.status.in_(("APPROVED", "REJECTED")),
    ).order_by(WorkflowTask.actioned_at.desc(), WorkflowTask.id.desc()))
    now = _now()
    if instance.status == "COMPLETED":
        request.status = "APPROVED"
        request.approved_by = final_task.actioned_by if final_task else None
        request.approved_at = final_task.actioned_at if final_task else now
    elif instance.status == "TERMINATED":
        request.status = "REJECTED"
        request.rejected_by = final_task.actioned_by if final_task else None
        request.rejected_at = final_task.actioned_at if final_task else now
        request.rejection_reason = final_task.comment if final_task else None
    request.updated_at = now
    from app.services.notification import notify
    result_label = "已批准" if instance.status == "COMPLETED" else "被驳回"
    notification_type = "PURCHASE_APPROVED" if instance.status == "COMPLETED" else "PURCHASE_REJECTED"
    notify(db, request.requester_id, notification_type, "采购审批结果",
           f"采购单 {request.request_number} {result_label}", "PURCHASE_REQUEST", request.id)


from app.services import workflow as workflow_service

workflow_service.register_callback("PURCHASE_REQUEST", _purchase_workflow_callback)


def _create_object(db: Session, item: AssetReceive, operator: UUID | None,
                   owner_org_id: UUID | None, operator_org_id: UUID | None) -> InfrastructureObject:
    if db.scalar(select(ObjectType.id).where(ObjectType.id == item.object_type_id, ObjectType.deleted_at.is_(None))) is None:
        raise ServiceError(400, "InvalidObjectType", "对象类型不存在")
    obj = InfrastructureObject(
        object_type_id=item.object_type_id, name=item.name, serial_number=item.serial_number,
        asset_number=item.asset_number, manufacturer=item.manufacturer, model=item.model,
        status="PLANNED", ownership="OWNED", management_scope="NO_ACCESS",
        owner_org_id=owner_org_id, operator_org_id=operator_org_id,
        maintainer_org_id=item.maintainer_org_id, created_by=operator, updated_by=operator,
    )
    db.add(obj)
    db.flush()
    db.add(ObjectSpec(object_id=obj.id, spec_data=item.spec_data or {}, data_source="MANUAL", confidence="HIGH", data_status="NORMAL", operator_id=operator))
    db.add(ObjectHistory(object_id=obj.id, change_type="CREATE", before_data=None, after_data={"name": obj.name, "status": obj.status}, source="API", confidence="HIGH", operator=operator))
    return obj


def receive_assets(db: Session, items: list[AssetReceive], user: User) -> list[Asset]:
    operator = _required_user(db, None, str(user.id), "验收操作人")
    results: list[Asset] = []
    for item in items:
        owner_org_id, operator_org_id = creation_organizations(
            db, user, item.owner_org_id, item.operator_org_id
        )
        purchase = db.get(PurchaseRequest, item.purchase_request_id)
        if purchase is None:
            raise ServiceError(404, "PurchaseRequestNotFound", "采购申请不存在")
        if purchase.status != "APPROVED":
            raise ServiceError(409, "PurchaseNotApproved", "采购申请未批准，不能到货验收")
        obj = db.scalar(select(InfrastructureObject).where(InfrastructureObject.id == item.object_id, InfrastructureObject.deleted_at.is_(None))) if item.object_id else _create_object(db, item, operator, owner_org_id, operator_org_id)
        if obj is None:
            raise ServiceError(404, "ObjectNotFound", "关联对象不存在")
        if item.object_id:
            require_organization_write_access(db, user, obj)
        if db.scalar(select(Asset.id).where(Asset.object_id == obj.id, Asset.deleted_at.is_(None))):
            raise ServiceError(409, "ObjectAlreadyHasAsset", "对象已关联资产记录")
        asset = Asset(
            object_id=obj.id, asset_number=item.asset_number, lifecycle_status="RECEIVED",
            purchase_request_id=item.purchase_request_id, purchase_order_id=item.purchase_order_id,
            purchase_date=item.purchase_date, received_date=item.received_date or date.today(),
            vendor=item.vendor or purchase.preferred_vendor, contract_number=item.contract_number,
            warranty_start_date=item.warranty_start_date, warranty_end_date=item.warranty_end_date,
            warranty_provider=item.warranty_provider, service_level=item.service_level,
            cost=item.cost, currency=item.currency or purchase.currency,
            owner_org_id=owner_org_id if not has_global_resource_access(db, user) else item.owner_org_id or obj.owner_org_id,
            operator_org_id=operator_org_id if not has_global_resource_access(db, user) else item.operator_org_id or obj.operator_org_id,
            maintainer_org_id=item.maintainer_org_id or obj.maintainer_org_id,
            created_by=operator, updated_by=operator,
        )
        obj.asset_number = item.asset_number
        db.add(asset)
        db.flush()
        _history(db, asset, "APPROVED", "RECEIVED", operator, purchase_request_id=str(purchase.id))
        results.append(asset)
    db.commit()
    for asset in results:
        db.refresh(asset)
    return results


def create_inventory_location(db: Session, payload: InventoryLocationCreate) -> InventoryLocation:
    item = InventoryLocation(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def stock_asset(db: Session, asset_id: UUID, payload: StockAsset, user: User) -> Asset:
    asset = _active_asset(db, asset_id)
    require_organization_write_access(db, user, asset)
    _require_transition(asset, "STOCK")
    _require_version(asset, payload.version)
    location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == payload.inventory_location_id, InventoryLocation.deleted_at.is_(None)))
    if location is None:
        raise ServiceError(404, "InventoryLocationNotFound", "库存位置不存在")
    operator = _required_user(db, payload.operator_id, str(user.id), "库存操作人")
    old = asset.lifecycle_status
    asset.lifecycle_status, asset.inventory_location_id = "STOCK", location.id
    asset.version += 1
    asset.updated_by = operator
    db.add(InventoryRecord(transaction_type="IN", asset_id=asset.id, quantity=1, warehouse_location=f"{location.warehouse}/{location.shelf or location.location_code}", inventory_location_id=location.id, related_purchase_order_id=asset.purchase_order_id, operator_id=operator, notes=payload.notes))
    _history(db, asset, old, "STOCK", operator, inventory_location_id=str(location.id))
    db.commit()
    db.refresh(asset)
    return asset


def transfer_asset(db: Session, asset_id: UUID, payload: TransferAsset, user: User) -> Asset:
    asset = _active_asset(db, asset_id)
    require_organization_write_access(db, user, asset)
    _require_transition(asset, "TRANSFERRED")
    _require_version(asset, payload.version)
    if payload.target_organization_id is not None:
        if db.scalar(select(Organization.id).where(Organization.id == payload.target_organization_id, Organization.deleted_at.is_(None))) is None:
            raise ServiceError(404, "OrganizationNotFound", "目标组织不存在")
    operator = _required_user(db, payload.operator_id, str(user.id), "调拨操作人")
    old, old_location = asset.lifecycle_status, asset.inventory_location_id
    if old_location is not None:
        db.add(InventoryRecord(
            transaction_type="OUT", asset_id=asset.id, quantity=-1,
            inventory_location_id=old_location, related_purchase_order_id=asset.purchase_order_id,
            operator_id=operator, notes=payload.notes,
        ))
    asset.lifecycle_status, asset.inventory_location_id = "TRANSFERRED", None
    if payload.target_organization_id is not None:
        asset.operator_org_id = payload.target_organization_id
    asset.version += 1
    asset.updated_by = operator
    _history(db, asset, old, "TRANSFERRED", operator,
             target_organization_id=str(payload.target_organization_id) if payload.target_organization_id else None,
             source_inventory_location_id=str(old_location) if old_location else None, notes=payload.notes)
    db.commit()
    db.refresh(asset)
    return asset


def complete_transfer(db: Session, asset_id: UUID, payload: CompleteTransfer, user: User) -> Asset:
    asset = _active_asset(db, asset_id)
    require_organization_write_access(db, user, asset)
    if asset.lifecycle_status not in {"TRANSFERRED", "RECOVERED"}:
        raise ServiceError(409, "InvalidAssetTransition", f"资产状态 {asset.lifecycle_status} 不能转换为 STOCK")
    return stock_asset(db, asset_id, payload, user)


def retire_asset(db: Session, asset_id: UUID, payload: RetireAsset, user: User) -> Asset:
    asset = _active_asset(db, asset_id)
    require_organization_write_access(db, user, asset)
    _require_transition(asset, "RETIRED")
    _require_version(asset, payload.version)
    operator = _required_user(db, payload.operator_id, str(user.id), "退役操作人")
    obj = db.get(InfrastructureObject, asset.object_id)
    old = asset.lifecycle_status
    asset.lifecycle_status, asset.inventory_location_id = "RETIRED", None
    asset.version += 1
    asset.updated_by = operator
    obj.status, obj.updated_by = "RETIRED", operator
    if payload.end_active_relationships:
        relationships = db.scalars(select(ObjectRelationship).where(
            ObjectRelationship.source_object_id == obj.id,
            ObjectRelationship.status == "ACTIVE",
            ObjectRelationship.deleted_at.is_(None),
        )).all()
        for relationship in relationships:
            relationship.status = "INACTIVE"
        obj.deployed_location_id = None
    _history(db, asset, old, "RETIRED", operator, reason=payload.reason,
             disposition=payload.disposition,
             ended_active_relationships=payload.end_active_relationships)
    db.commit()
    db.refresh(asset)
    return asset


def recover_asset(db: Session, asset_id: UUID, payload: RecoverAsset, user: User) -> Asset:
    asset = _active_asset(db, asset_id)
    require_organization_write_access(db, user, asset)
    _require_transition(asset, "RECOVERED")
    _require_version(asset, payload.version)
    operator = _required_user(db, payload.operator_id, str(user.id), "退役撤销操作人")
    obj = db.get(InfrastructureObject, asset.object_id)
    old = asset.lifecycle_status
    asset.lifecycle_status = "RECOVERED"
    asset.version += 1
    asset.updated_by = operator
    # Recovery removes the terminal object state, but does not claim that the
    # equipment is operational before it has been inspected or redeployed.
    obj.status, obj.updated_by = "MAINTENANCE", operator
    _history(db, asset, old, "RECOVERED", operator, reason=payload.reason)
    db.commit()
    db.refresh(asset)
    return asset


def deploy_asset(db: Session, asset_id: UUID, payload: DeployAsset, user: User) -> Asset:
    asset = _active_asset(db, asset_id)
    require_organization_write_access(db, user, asset)
    # The Phase 3 deploy action intentionally collapses transport/install into one
    # accepted deployment while retaining DEPLOYED and ACTIVE as separate events.
    _require_transition(asset, "DEPLOYED")
    _require_version(asset, payload.version)
    obj = db.get(InfrastructureObject, asset.object_id)
    location = db.scalar(select(InfrastructureObject).where(InfrastructureObject.id == payload.location_id, InfrastructureObject.deleted_at.is_(None)))
    rack_type = db.scalar(select(ObjectType.name).where(ObjectType.id == location.object_type_id)) if location else None
    if location is None or rack_type != "RACK":
        raise ServiceError(422, "InvalidDeploymentLocation", "部署位置必须是有效的 Rack 对象")
    require_organization_write_access(db, user, location)
    relation_type = db.scalar(select(RelationshipType).where(RelationshipType.name == "installed_in", RelationshipType.deleted_at.is_(None)))
    if relation_type is None:
        raise ServiceError(409, "RelationshipTypeMissing", "缺少 installed_in 关系类型")
    operator = _required_user(db, payload.deployed_by, str(user.id), "部署操作人")
    deployment = Deployment(asset_id=asset.id, object_id=obj.id, location_id=location.id, deployment_type=payload.deployment_type, status="COMPLETED", acceptance_status="ACCEPTED", deployed_by=operator, deployed_at=_now(), notes=payload.notes)
    db.add(deployment)
    db.flush()
    db.add(InventoryRecord(transaction_type="OUT", asset_id=asset.id, quantity=-1, inventory_location_id=asset.inventory_location_id, related_purchase_order_id=asset.purchase_order_id, related_deployment_id=deployment.id, operator_id=operator, notes=payload.notes))
    _history(db, asset, "STOCK", "DEPLOYED", operator, location_id=str(location.id), deployment_id=str(deployment.id))
    _history(db, asset, "DEPLOYED", "ACTIVE", operator, location_id=str(location.id), deployment_id=str(deployment.id))
    asset.lifecycle_status, asset.inventory_location_id = "ACTIVE", None
    asset.version += 1
    asset.updated_by = operator
    obj.deployed_location_id, obj.status, obj.updated_by = location.id, "ACTIVE", operator
    existing = db.scalar(select(ObjectRelationship).where(ObjectRelationship.source_object_id == obj.id, ObjectRelationship.relation_type_id == relation_type.id, ObjectRelationship.deleted_at.is_(None)))
    if existing:
        existing.target_object_id, existing.status = location.id, "ACTIVE"
    else:
        db.add(ObjectRelationship(source_object_id=obj.id, relation_type_id=relation_type.id, target_object_id=location.id, attributes={"deployment_id": str(deployment.id)}, status="ACTIVE", confidence="HIGH", data_source="MANUAL", created_by=operator))
    db.commit()
    db.refresh(asset)
    return asset


def asset_out(db: Session, asset: Asset, detail: bool = False) -> dict[str, Any]:
    obj = db.get(InfrastructureObject, asset.object_id)
    data = {key: getattr(asset, key) for key in (
        "id", "object_id", "asset_number", "lifecycle_status", "purchase_request_id",
        "purchase_order_id", "purchase_date", "received_date", "vendor", "contract_number",
        "warranty_start_date", "warranty_end_date", "warranty_provider", "service_level",
        "cost", "currency", "owner_org_id", "operator_org_id", "maintainer_org_id",
        "inventory_location_id", "version", "created_at", "updated_at")}
    data["object"] = {"id": obj.id, "name": obj.name, "object_type_id": obj.object_type_id, "serial_number": obj.serial_number, "model": obj.model, "status": obj.status, "deployed_location_id": obj.deployed_location_id}
    if detail:
        spec = db.scalar(select(ObjectSpec).where(ObjectSpec.object_id == obj.id, ObjectSpec.deleted_at.is_(None)))
        location = db.get(InventoryLocation, asset.inventory_location_id) if asset.inventory_location_id else None
        deployment = db.scalar(select(Deployment).where(Deployment.asset_id == asset.id).order_by(Deployment.created_at.desc()))
        data.update(
            spec=spec.spec_data if spec else {},
            inventory_location=({key: getattr(location, key) for key in ("id", "name", "warehouse", "shelf", "location_code")} if location else None),
            deployment=({key: getattr(deployment, key) for key in ("id", "location_id", "deployment_type", "status", "acceptance_status", "deployed_by", "deployed_at", "notes")} if deployment else None),
        )
    return data


def list_assets(db: Session, lifecycle_status: str | None, organization_id: UUID | None, location_id: UUID | None, page: int, page_size: int, user: User) -> tuple[int, list[Asset]]:
    filters = [Asset.deleted_at.is_(None)]
    if not has_global_resource_access(db, user):
        filters.append(organization_scope(Asset, user.organization_id))
    if lifecycle_status: filters.append(Asset.lifecycle_status == lifecycle_status)
    if organization_id: filters.append(or_(Asset.owner_org_id == organization_id, Asset.operator_org_id == organization_id, Asset.maintainer_org_id == organization_id))
    query = select(Asset)
    if location_id:
        query = query.join(InfrastructureObject, InfrastructureObject.id == Asset.object_id)
        filters.append(or_(Asset.inventory_location_id == location_id, InfrastructureObject.deployed_location_id == location_id))
    total = db.scalar(select(func.count()).select_from(query.where(*filters).subquery())) or 0
    return total, list(db.scalars(query.where(*filters).order_by(Asset.created_at.desc()).offset((page-1)*page_size).limit(page_size)))


def lifecycle(db: Session, asset_id: UUID) -> list[dict[str, Any]]:
    asset = _active_asset(db, asset_id)
    events: list[dict[str, Any]] = []
    purchase = db.get(PurchaseRequest, asset.purchase_request_id) if asset.purchase_request_id else None
    if purchase:
        events.append({"event_type": "REQUESTED", "occurred_at": purchase.created_at, "details": {"purchase_request_id": str(purchase.id)}})
        if purchase.approved_at: events.append({"event_type": "APPROVED", "occurred_at": purchase.approved_at, "details": {"approved_by": str(purchase.approved_by) if purchase.approved_by else None}})
    histories = db.scalars(select(ObjectHistory).where(ObjectHistory.object_id == asset.object_id, ObjectHistory.deleted_at.is_(None)).order_by(ObjectHistory.created_at)).all()
    for item in histories:
        status = (item.after_data or {}).get("lifecycle_status")
        if status: events.append({"event_type": status, "occurred_at": item.created_at, "details": item.after_data})
    return sorted(events, key=lambda event: event["occurred_at"])
