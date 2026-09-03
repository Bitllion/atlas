"""Response contracts for object import operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportErrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    row: int
    field: str | None
    error_type: str
    message: str


class ImportResult(BaseModel):
    import_id: UUID
    status: str
    total_count: int
    success_count: int
    failed_count: int
    errors: list[ImportErrorOut]
    dry_run: bool


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    filename: str
    format: str
    total_rows: int
    success_count: int
    failed_count: int
    status: str
    error_summary: dict | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    version: int
