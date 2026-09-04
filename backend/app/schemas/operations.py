"""Pydantic contracts for operations APIs."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class WorkOrderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: Literal["FAULT", "REPAIR", "INSPECTION", "CHANGE"]
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    object_id: UUID | None = None
    related_object_id: UUID | None = None
    description: str | None = None
    fault_record_id: UUID | None = None

    @model_validator(mode="after")
    def require_object(self):
        if self.object_id is None and self.related_object_id is None:
            raise ValueError("工单必须关联基础设施对象")
        if self.object_id is not None and self.related_object_id is not None and self.object_id != self.related_object_id:
            raise ValueError("object_id 与 related_object_id 不一致")
        return self


class WorkOrderAssign(BaseModel):
    assignee_id: UUID | None = None
    assigned_to: UUID | None = None


class RepairCreate(BaseModel):
    object_id: UUID | None = None
    repair_type: Literal["REPLACEMENT", "UPGRADE", "ADJUSTMENT", "CLEANING"]
    description: str = Field(min_length=1)
    parts_used: list[Any] | None = None
    repair_result: Literal["SUCCESS", "FAILED", "PARTIAL"]
    engineer_id: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    verification_notes: str | None = None


class ReplacementCreate(BaseModel):
    repair_record_id: UUID | None = None
    old_object_id: UUID
    new_object_id: UUID
    replacement_reason: Literal["FAILURE", "UPGRADE", "PREVENTIVE"]
    old_object_disposition: Literal["RETIRED", "RMA", "STOCK", "SCRAPPED"]
    engineer_id: UUID | None = None
    replaced_at: datetime | None = None
    notes: str | None = None
