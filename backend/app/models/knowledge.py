"""Knowledge article, relation, and attachment persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin


class KnowledgeArticle(IdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_articles"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','UNDER_REVIEW','PUBLISHED','ARCHIVED')", name="ck_knowledge_articles_status"),
        CheckConstraint("type IN ('SOP','TROUBLESHOOTING','FAQ','BEST_PRACTICE')", name="ck_knowledge_articles_type"),
        Index("idx_knowledge_articles_status", "status", text("published_at DESC"), postgresql_where=text("deleted_at IS NULL")),
        Index("idx_knowledge_articles_type", "type", postgresql_where=text("status = 'PUBLISHED' AND deleted_at IS NULL")),
        Index("idx_knowledge_articles_tags", "tags", postgresql_using="gin"),
    )

    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", server_default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    reviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None]
    published_at: Mapped[datetime | None]
    archived_at: Mapped[datetime | None]
    tags: Mapped[list | None] = mapped_column(JSONB)


class KnowledgeRelation(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "knowledge_relations"
    __table_args__ = (
        CheckConstraint("related_type IN ('OBJECT','WORK_ORDER','FAULT','REPAIR')", name="ck_knowledge_relations_type"),
        UniqueConstraint("article_id", "related_type", "related_id", name="uq_knowledge_relations_target"),
        Index("idx_knowledge_relations_article", "article_id"),
        Index("idx_knowledge_relations_related", "related_type", "related_id"),
    )

    article_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_articles.id", ondelete="CASCADE"))
    related_type: Mapped[str] = mapped_column(String(50))
    related_id: Mapped[UUID]
    relation_reason: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class ArticleAttachment(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "article_attachments"
    __table_args__ = (Index("idx_article_attachments_article", "article_id"),)

    article_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_articles.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_size: Mapped[int] = mapped_column(Integer)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
