"""Knowledge article business logic and serialization."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.exceptions import ServiceError
from app.models import ArticleAttachment, InfrastructureObject, KnowledgeArticle, KnowledgeRelation, User
from app.schemas.knowledge import ArticleCreate, ArticleUpdate, ObjectLinks


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def operator_id(db: Session, value: str | None) -> UUID:
    if not value:
        raise ServiceError(400, "UserRequired", "必须提供 X-User-Id")
    try:
        user_id = UUID(value)
    except ValueError as exc:
        raise ServiceError(400, "InvalidUser", "X-User-Id 必须是 UUID") from exc
    if db.scalar(select(User.id).where(User.id == user_id, User.deleted_at.is_(None))) is None:
        raise ServiceError(400, "InvalidUser", "用户不存在")
    return user_id


def active_article(db: Session, article_id: UUID) -> KnowledgeArticle:
    article = db.scalar(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id, KnowledgeArticle.deleted_at.is_(None)))
    if article is None:
        raise ServiceError(404, "ArticleNotFound", "知识文章不存在")
    return article


def article_out(article: KnowledgeArticle) -> dict[str, Any]:
    fields = ("id", "title", "content", "type", "status", "version", "is_latest", "author_id", "reviewer_id", "reviewed_at", "published_at", "archived_at", "tags", "created_at", "updated_at")
    return {field: getattr(article, field) for field in fields}


def attachment_out(item: ArticleAttachment) -> dict[str, Any]:
    return {field: getattr(item, field) for field in ("id", "article_id", "file_name", "file_path", "file_size", "uploaded_by", "created_at")}


def links_out(db: Session, article_id: UUID) -> list[dict[str, Any]]:
    rows = db.execute(
        select(KnowledgeRelation, InfrastructureObject)
        .outerjoin(InfrastructureObject, (KnowledgeRelation.related_type == "OBJECT") & (KnowledgeRelation.related_id == InfrastructureObject.id))
        .where(KnowledgeRelation.article_id == article_id)
        .order_by(KnowledgeRelation.created_at)
    ).all()
    return [{"id": rel.id, "related_type": rel.related_type, "related_id": rel.related_id, "relation_reason": rel.relation_reason, "created_at": rel.created_at, "object_name": obj.name if obj else None} for rel, obj in rows]


def detail(db: Session, article: KnowledgeArticle) -> dict[str, Any]:
    result = article_out(article)
    attachments = db.scalars(select(ArticleAttachment).where(ArticleAttachment.article_id == article.id).order_by(ArticleAttachment.created_at)).all()
    result["attachments"] = [attachment_out(item) for item in attachments]
    result["links"] = links_out(db, article.id)
    return result


def create(db: Session, payload: ArticleCreate, user: str | None) -> KnowledgeArticle:
    article = KnowledgeArticle(**payload.model_dump(), status="DRAFT", author_id=operator_id(db, user))
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def update(db: Session, article: KnowledgeArticle, payload: ArticleUpdate, user: str | None) -> KnowledgeArticle:
    operator_id(db, user)
    if article.status != "DRAFT":
        raise ServiceError(409, "ArticleNotEditable", "仅草稿状态文章可直接编辑")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, key, value)
    article.version += 1
    article.updated_at = _now()
    db.commit()
    db.refresh(article)
    return article


def publish(db: Session, article: KnowledgeArticle, user: str | None) -> KnowledgeArticle:
    reviewer = operator_id(db, user)
    if article.status not in {"DRAFT", "UNDER_REVIEW"}:
        raise ServiceError(409, "InvalidArticleTransition", "仅草稿或审核中文章可发布")
    now = _now()
    article.status = "PUBLISHED"
    article.reviewer_id = reviewer
    article.reviewed_at = now
    article.published_at = now
    article.updated_at = now
    db.commit()
    db.refresh(article)
    return article


def link_objects(db: Session, article: KnowledgeArticle, payload: ObjectLinks, user: str | None) -> list[dict[str, Any]]:
    creator = operator_id(db, user)
    object_ids = set(payload.objects)
    existing_objects = set(db.scalars(select(InfrastructureObject.id).where(InfrastructureObject.id.in_(object_ids), InfrastructureObject.deleted_at.is_(None))).all())
    missing = object_ids - existing_objects
    if missing:
        raise ServiceError(400, "InvalidObject", "关联对象不存在", object_ids=[str(item) for item in sorted(missing, key=str)])
    existing_links = set(db.scalars(select(KnowledgeRelation.related_id).where(KnowledgeRelation.article_id == article.id, KnowledgeRelation.related_type == "OBJECT", KnowledgeRelation.related_id.in_(object_ids))).all())
    for object_id in object_ids - existing_links:
        db.add(KnowledgeRelation(article_id=article.id, related_type="OBJECT", related_id=object_id, relation_reason=payload.relation_reason, created_by=creator))
    db.commit()
    return links_out(db, article.id)


def unlink_objects(db: Session, article: KnowledgeArticle, payload: ObjectLinks, user: str | None) -> list[dict[str, Any]]:
    operator_id(db, user)
    links = db.scalars(select(KnowledgeRelation).where(KnowledgeRelation.article_id == article.id, KnowledgeRelation.related_type == "OBJECT", KnowledgeRelation.related_id.in_(payload.objects))).all()
    for link in links:
        db.delete(link)
    db.commit()
    return links_out(db, article.id)


def upload(db: Session, article: KnowledgeArticle, file: UploadFile, user: str | None) -> ArticleAttachment:
    uploader = operator_id(db, user)
    original_name = Path(file.filename or "attachment").name
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    article_dir = root / str(article.id)
    article_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}_{original_name}"
    target = article_dir / stored_name
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                output.write(chunk)
        relative_path = str(target.relative_to(root.parent))
        attachment = ArticleAttachment(article_id=article.id, file_name=original_name, file_path=relative_path, file_size=size, uploaded_by=uploader)
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
