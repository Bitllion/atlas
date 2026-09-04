"""Create Phase 5a knowledge tables.

Revision ID: 0006_knowledge_tables
Revises: 0005_operations_tables
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_knowledge_tables"
down_revision: Union[str, None] = "0005_operations_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "knowledge_articles",
        sa.Column("id", UUID, primary_key=True), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False), sa.Column("type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("author_id", UUID, nullable=False), sa.Column("reviewer_id", UUID),
        sa.Column("reviewed_at", sa.DateTime()), sa.Column("published_at", sa.DateTime()), sa.Column("archived_at", sa.DateTime()),
        sa.Column("tags", JSONB), sa.Column("deleted_at", sa.DateTime()), sa.Column("deleted_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]), sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.CheckConstraint("status IN ('DRAFT','UNDER_REVIEW','PUBLISHED','ARCHIVED')", name="ck_knowledge_articles_status"),
        sa.CheckConstraint("type IN ('SOP','TROUBLESHOOTING','FAQ','BEST_PRACTICE')", name="ck_knowledge_articles_type"),
    )
    op.create_index("idx_knowledge_articles_status", "knowledge_articles", ["status", sa.text("published_at DESC")], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_knowledge_articles_type", "knowledge_articles", ["type"], postgresql_where=sa.text("status = 'PUBLISHED' AND deleted_at IS NULL"))
    op.create_index("idx_knowledge_articles_tags", "knowledge_articles", ["tags"], postgresql_using="gin")

    op.create_table(
        "knowledge_relations",
        sa.Column("id", UUID, primary_key=True), sa.Column("article_id", UUID, nullable=False),
        sa.Column("related_type", sa.String(50), nullable=False), sa.Column("related_id", UUID, nullable=False),
        sa.Column("relation_reason", sa.String(255)), sa.Column("created_by", UUID),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["article_id"], ["knowledge_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint("related_type IN ('OBJECT','WORK_ORDER','FAULT','REPAIR')", name="ck_knowledge_relations_type"),
        sa.UniqueConstraint("article_id", "related_type", "related_id", name="uq_knowledge_relations_target"),
    )
    op.create_index("idx_knowledge_relations_article", "knowledge_relations", ["article_id"])
    op.create_index("idx_knowledge_relations_related", "knowledge_relations", ["related_type", "related_id"])

    op.create_table(
        "article_attachments",
        sa.Column("id", UUID, primary_key=True), sa.Column("article_id", UUID, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False), sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("uploaded_by", UUID, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["article_id"], ["knowledge_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
    )
    op.create_index("idx_article_attachments_article", "article_attachments", ["article_id"])


def downgrade() -> None:
    op.drop_table("article_attachments")
    op.drop_table("knowledge_relations")
    op.drop_table("knowledge_articles")
