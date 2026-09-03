"""Persistence models for two-phase file imports."""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin


class ImportJob(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint("format IN ('XLSX', 'CSV')", name="ck_import_jobs_format"),
        CheckConstraint("status IN ('PREVIEWING', 'PREVIEWED', 'EXECUTING', 'SUCCEEDED', 'PARTIAL_FAILED', 'FAILED')", name="ck_import_jobs_status"),
        Index("idx_import_jobs_status_created", "status", "created_at"),
        Index("idx_import_jobs_created_by", "created_by"),
        Index("idx_import_jobs_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

    name: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    format: Mapped[str] = mapped_column(String(20))
    total_rows: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    success_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(50))
    preview_data: Mapped[dict | None] = mapped_column(JSONB)
    error_summary: Mapped[dict | None] = mapped_column(JSONB)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class ImportError(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "import_errors"
    __table_args__ = (Index("idx_import_errors_job_row", "import_job_id", "row_number"),)

    import_job_id: Mapped[UUID] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"))
    row_number: Mapped[int] = mapped_column(Integer)
    field: Mapped[str | None] = mapped_column(String(255))
    error_type: Mapped[str] = mapped_column(String(100))
    error_message: Mapped[str] = mapped_column(Text)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
