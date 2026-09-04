"""Create in-app notifications.

Revision ID: 0008_notifications
Revises: 0007_workflow_tables
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0008_notifications"
down_revision: Union[str, None] = "0007_workflow_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("recipient_id", UUID, nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(100)),
        sa.Column("entity_id", UUID),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime()),
        sa.Column("deleted_by", UUID),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
    )
    op.create_index(
        "idx_notifications_recipient_unread_created", "notifications",
        ["recipient_id", "is_read", sa.text("created_at DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
