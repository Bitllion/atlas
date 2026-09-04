"""HTTP routes for Phase 5a knowledge management."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.config.settings import settings
from app.core.exceptions import ServiceError
from app.core.security import actor_id, get_current_user_optional
from app.models import ArticleAttachment, KnowledgeArticle, User
from app.schemas.knowledge import ArticleCreate, ArticleStatus, ArticleType, ArticleUpdate, ObjectLinks
from app.services import knowledge as service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/articles", status_code=status.HTTP_201_CREATED)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.article_out(service.create(db, payload, actor_id(user)))


@router.get("/articles")
def list_articles(article_type: ArticleType | None = Query(default=None, alias="type"), article_status: ArticleStatus | None = Query(default=None, alias="status"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    filters = [KnowledgeArticle.deleted_at.is_(None), KnowledgeArticle.is_latest.is_(True)]
    if article_type:
        filters.append(KnowledgeArticle.type == article_type)
    if article_status:
        filters.append(KnowledgeArticle.status == article_status)
    total = db.scalar(select(func.count()).select_from(KnowledgeArticle).where(*filters)) or 0
    items = db.scalars(select(KnowledgeArticle).where(*filters).order_by(KnowledgeArticle.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [service.article_out(item) for item in items]}


@router.get("/articles/{article_id}")
def get_article(article_id: UUID, db: Session = Depends(get_db)):
    return service.detail(db, service.active_article(db, article_id))


@router.put("/articles/{article_id}")
def update_article(article_id: UUID, payload: ArticleUpdate, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.article_out(service.update(db, service.active_article(db, article_id), payload, actor_id(user)))


@router.post("/articles/{article_id}/publish")
def publish_article(article_id: UUID, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.article_out(service.publish(db, service.active_article(db, article_id), actor_id(user)))


@router.post("/articles/{article_id}/attachments", status_code=status.HTTP_201_CREATED)
def upload_attachment(article_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return service.attachment_out(service.upload(db, service.active_article(db, article_id), file, actor_id(user)))


@router.get("/articles/{article_id}/attachments/{attachment_id}/download")
def download_attachment(article_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
    service.active_article(db, article_id)
    attachment = db.scalar(
        select(ArticleAttachment).where(
            ArticleAttachment.id == attachment_id,
            ArticleAttachment.article_id == article_id,
        )
    )
    if attachment is None:
        raise ServiceError(404, "AttachmentNotFound", "附件不存在")

    upload_root = Path(settings.upload_dir)
    if not upload_root.is_absolute():
        upload_root = Path(__file__).resolve().parents[3] / upload_root
    upload_root = upload_root.resolve()
    stored_path = Path(attachment.file_path)
    candidates = [upload_root / stored_path, upload_root.parent / stored_path]
    target = next(
        (candidate.resolve() for candidate in candidates if candidate.resolve().is_relative_to(upload_root) and candidate.is_file()),
        None,
    )
    if target is None:
        raise ServiceError(404, "AttachmentFileNotFound", "附件文件不存在")
    return FileResponse(target, filename=attachment.file_name)


@router.post("/articles/{article_id}/link-objects")
def link_objects(article_id: UUID, payload: ObjectLinks, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return {"items": service.link_objects(db, service.active_article(db, article_id), payload, actor_id(user))}


@router.delete("/articles/{article_id}/link-objects")
def unlink_objects(article_id: UUID, payload: ObjectLinks, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return {"items": service.unlink_objects(db, service.active_article(db, article_id), payload, actor_id(user))}


@router.get("/articles/{article_id}/links")
def get_links(article_id: UUID, db: Session = Depends(get_db)):
    article = service.active_article(db, article_id)
    return {"items": service.links_out(db, article.id)}
