"""Pydantic contracts for Infrastructure Core."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ObjectStatus = Literal["PLANNED", "ACTIVE", "INACTIVE", "MAINTENANCE", "RETIRED"]
Ownership = Literal["OWNED", "CUSTOMER_OWNED", "THIRD_PARTY"]
ManagementScope = Literal["FULL_CONTROL", "HARDWARE_ONLY", "MAINTENANCE_ONLY", "NO_ACCESS"]


class ObjectCreate(BaseModel):
    object_type_id: UUID
    name: str = Field(min_length=1, max_length=255)
    serial_number: str | None = None
    asset_number: str | None = None
    uuid: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    hardware_generation: str | None = None
    status: ObjectStatus = "PLANNED"
    ownership: Ownership = "OWNED"
    management_scope: ManagementScope = "NO_ACCESS"
    owner_org_id: UUID | None = None
    operator_org_id: UUID | None = None
    maintainer_org_id: UUID | None = None
    deployed_location_id: UUID | None = None
    spec_data: dict[str, Any] | None = None


class ObjectUpdate(BaseModel):
    version: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    serial_number: str | None = None
    asset_number: str | None = None
    uuid: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    hardware_generation: str | None = None
    status: ObjectStatus | None = None
    ownership: Ownership | None = None
    management_scope: ManagementScope | None = None
    owner_org_id: UUID | None = None
    operator_org_id: UUID | None = None
    maintainer_org_id: UUID | None = None
    deployed_location_id: UUID | None = None
    spec_data: dict[str, Any] | None = None


class ObjectTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    category: str
    description: str | None


class ObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    object_type_id: UUID
    name: str
    serial_number: str | None
    asset_number: str | None
    uuid: str | None
    manufacturer: str | None
    model: str | None
    firmware_version: str | None
    hardware_generation: str | None
    status: str
    ownership: str
    management_scope: str
    owner_org_id: UUID | None
    operator_org_id: UUID | None
    maintainer_org_id: UUID | None
    deployed_location_id: UUID | None
    version: int
    created_at: datetime
    updated_at: datetime


class ObjectDetail(ObjectOut):
    object_type: ObjectTypeOut
    spec_data: dict[str, Any]
    relationship_summary: dict[str, int]


class RelationshipCreate(BaseModel):
    source_object_id: UUID
    relationship_type_id: UUID
    target_object_id: UUID
    attributes: dict[str, Any] | None = None
    status: Literal["ACTIVE", "INACTIVE", "REMOVED"] = "ACTIVE"
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    data_source: str = "MANUAL"


class RelationshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source_object_id: UUID
    relationship_type_id: UUID
    target_object_id: UUID
    attributes: dict[str, Any] | None
    status: str
    confidence: str
    data_source: str
    created_at: datetime
    updated_at: datetime


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    object_id: UUID
    change_type: str
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    source: str
    operator: UUID | None
    created_at: datetime
