"""Pydantic contracts for asset lifecycle APIs."""

from datetime import date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PurchaseItem(BaseModel):
    object_type_id: UUID
    quantity: int = Field(ge=1)
    model: str | None = None
    unit_budget: Decimal | None = Field(default=None, ge=0)
    vendor: str | None = None


class PurchaseRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    items: list[PurchaseItem] = Field(min_length=1)
    estimated_cost: Decimal | None = Field(default=None, ge=0)
    currency: str = "CNY"
    justification: str | None = None
    preferred_vendor: str | None = None
    requester_id: UUID | None = None


class PurchaseDecision(BaseModel):
    approved_by: UUID | None = None
    comment: str | None = None
    workflow_task_id: UUID | None = None


class PurchaseRejection(BaseModel):
    rejected_by: UUID | None = None
    rejection_reason: str = Field(min_length=1)
    workflow_task_id: UUID | None = None


class AssetReceive(BaseModel):
    asset_number: str = Field(min_length=1, max_length=255)
    purchase_request_id: UUID
    purchase_order_id: UUID | None = None
    object_id: UUID | None = None
    object_type_id: UUID | None = None
    name: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    spec_data: dict[str, Any] | None = None
    received_date: date | None = None
    purchase_date: date | None = None
    vendor: str | None = None
    contract_number: str | None = None
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    warranty_provider: str | None = None
    service_level: str | None = None
    cost: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    owner_org_id: UUID | None = None
    operator_org_id: UUID | None = None
    maintainer_org_id: UUID | None = None

    @model_validator(mode="after")
    def object_reference_or_definition(self):
        if self.object_id is None and (self.object_type_id is None or not self.name):
            raise ValueError("必须提供 object_id，或同时提供 object_type_id 和 name")
        return self


class InventoryLocationCreate(BaseModel):
    name: str
    warehouse: str
    shelf: str | None = None
    location_code: str
    organization_id: UUID | None = None
    description: str | None = None


class StockAsset(BaseModel):
    inventory_location_id: UUID
    operator_id: UUID | None = None
    notes: str | None = None
    version: int | None = Field(default=None, ge=1)


class DeployAsset(BaseModel):
    location_id: UUID
    deployed_by: UUID | None = None
    deployment_type: Literal["NEW", "TRANSFER", "REPLACEMENT"] = "NEW"
    notes: str | None = None
    version: int | None = Field(default=None, ge=1)


class InventoryReceive(StockAsset):
    asset_id: UUID


class DeploymentCreate(DeployAsset):
    asset_id: UUID


class TransferAsset(BaseModel):
    target_organization_id: UUID | None = None
    operator_id: UUID | None = None
    notes: str | None = None
    version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def target_or_notes(self):
        if self.target_organization_id is None and not self.notes:
            raise ValueError("必须提供目标组织或调拨备注")
        return self


class CompleteTransfer(StockAsset):
    pass


class RetireAsset(BaseModel):
    reason: str = Field(min_length=1)
    disposition: Literal["RMA", "SCRAPPED", "RETURNED_TO_VENDOR"] = "SCRAPPED"
    end_active_relationships: bool = True
    operator_id: UUID | None = None
    version: int | None = Field(default=None, ge=1)


class RecoverAsset(BaseModel):
    reason: str = Field(min_length=1)
    operator_id: UUID | None = None
    version: int | None = Field(default=None, ge=1)
