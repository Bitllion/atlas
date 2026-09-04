"""HTTP routes for two-phase object imports."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.core.security import actor_id, get_current_user_optional, require_permission
from app.database.session import get_db
from app.models import ImportError, ImportJob, User
from app.schemas.imports import ImportJobOut, ImportResult
from app.services import imports as service

router = APIRouter(dependencies=[Depends(require_permission("import.execute"))])


def _result(db: Session, job: ImportJob, dry_run: bool) -> dict:
    errors = service.job_errors(db, job.id)
    return {"import_id": job.id, "status": job.status, "total_count": job.total_rows, "success_count": job.success_count, "failed_count": job.failed_count, "errors": [service.error_dict(item) for item in errors], "dry_run": dry_run}


@router.post("/import/preview", response_model=ImportResult, tags=["imports"])
def preview_import(file: UploadFile = File(...), import_type: str = Form("object"), user: User | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    content = file.file.read()
    if not content:
        raise ServiceError(400, "EmptyImportFile", "导入文件为空")
    job = service.preview(db, file.filename or "upload", content, import_type, actor_id(user))
    return _result(db, job, True)


@router.post("/import/{import_id}/execute", response_model=ImportResult, tags=["imports"])
def execute_import(import_id: UUID, user: User | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    job = service.execute(db, import_id, user)
    return _result(db, job, False)


@router.get("/import/history", tags=["imports"])
def import_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    total, items = service.history(db, page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [ImportJobOut.model_validate(item) for item in items]}


@router.get("/import/{import_id}/errors", tags=["imports"])
def import_errors(import_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    if db.scalar(select(ImportJob.id).where(ImportJob.id == import_id, ImportJob.deleted_at.is_(None))) is None:
        raise ServiceError(404, "ImportNotFound", "导入任务不存在")
    total = db.scalar(select(func.count()).select_from(ImportError).where(ImportError.import_job_id == import_id)) or 0
    items = list(db.scalars(select(ImportError).where(ImportError.import_job_id == import_id).order_by(ImportError.row_number, ImportError.created_at).offset((page - 1) * page_size).limit(page_size)))
    return {"total": total, "page": page, "page_size": page_size, "items": [service.error_dict(item) for item in items]}
