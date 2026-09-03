"""Create the Phase 1a core, permission, and governance tables.

Revision ID: 0002_core_tables
Revises: 0001_phase0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_core_tables"
down_revision: Union[str, None] = "0001_phase0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def _id() -> sa.Column:
    return sa.Column("id", UUID, primary_key=True)


def _timestamps(*, updated: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now())
    ]
    if updated:
        columns.append(
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
    return columns


def _soft_delete() -> list[sa.Column]:
    return [
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", UUID, nullable=True),
    ]


def _active_index(table: str) -> None:
    op.create_index(
        f"idx_{table}_active",
        table,
        ["id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def upgrade() -> None:
    op.create_table(
        "organizations",
        _id(),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("org_type", sa.String(50), nullable=False),
        sa.Column("parent_org_id", UUID, nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["parent_org_id"], ["organizations.id"]),
        sa.CheckConstraint(
            "org_type IN ('INTERNAL', 'CUSTOMER', 'VENDOR')",
            name="ck_organizations_org_type",
        ),
    )
    op.create_index("idx_organizations_type", "organizations", ["org_type", "is_active"])
    op.create_index("idx_organizations_parent", "organizations", ["parent_org_id"])
    _active_index("organizations")

    op.create_table(
        "users",
        _id(),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        *_soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
    )
    op.create_index("idx_users_org", "users", ["organization_id", "is_active"])
    op.create_index(
        "idx_users_email",
        "users",
        ["email"],
        postgresql_where=sa.text("is_active = TRUE AND deleted_at IS NULL"),
    )
    _active_index("users")

    op.create_table(
        "roles",
        _id(),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization_id", UUID, nullable=True),
        *_soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
    )
    op.create_index("idx_roles_organization", "roles", ["organization_id"])
    _active_index("roles")

    op.create_table(
        "permissions",
        _id(),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_soft_delete(),
        *_timestamps(updated=False),
    )
    op.create_index("idx_permissions_resource", "permissions", ["resource_type", "action"])
    _active_index("permissions")

    op.create_table(
        "object_types",
        _id(),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("schema", JSONB, nullable=True),
        *_soft_delete(),
        *_timestamps(),
        sa.CheckConstraint(
            "category IN ('IT', 'NETWORK', 'FACILITY', 'POWER')",
            name="ck_object_types_category",
        ),
    )
    _active_index("object_types")

    op.create_table(
        "relationship_types",
        _id(),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_directed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allowed_source_types", JSONB, nullable=True),
        sa.Column("allowed_target_types", JSONB, nullable=True),
        sa.Column("attributes_schema", JSONB, nullable=True),
        *_soft_delete(),
        *_timestamps(),
    )
    _active_index("relationship_types")

    op.create_table(
        "objects",
        _id(),
        sa.Column("object_type_id", UUID, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("serial_number", sa.String(255), nullable=True),
        sa.Column("asset_number", sa.String(255), nullable=True),
        sa.Column("uuid", sa.String(255), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("firmware_version", sa.String(100), nullable=True),
        sa.Column("hardware_generation", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PLANNED"),
        sa.Column("ownership", sa.String(50), nullable=False),
        sa.Column("management_scope", sa.String(50), nullable=False),
        sa.Column("owner_org_id", UUID, nullable=True),
        sa.Column("operator_org_id", UUID, nullable=True),
        sa.Column("maintainer_org_id", UUID, nullable=True),
        sa.Column("deployed_location_id", UUID, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        *_soft_delete(),
        *_timestamps(),
        sa.Column("created_by", UUID, nullable=True),
        sa.Column("updated_by", UUID, nullable=True),
        sa.ForeignKeyConstraint(["object_type_id"], ["object_types.id"]),
        sa.ForeignKeyConstraint(["owner_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["operator_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["maintainer_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["deployed_location_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.CheckConstraint(
            "status IN ('PLANNED', 'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'RETIRED')",
            name="ck_objects_status",
        ),
        sa.CheckConstraint(
            "ownership IN ('OWNED', 'CUSTOMER_OWNED', 'THIRD_PARTY')",
            name="ck_objects_ownership",
        ),
        sa.CheckConstraint(
            "management_scope IN ('FULL_CONTROL', 'HARDWARE_ONLY', "
            "'MAINTENANCE_ONLY', 'NO_ACCESS')",
            name="ck_objects_management_scope",
        ),
    )
    op.create_index(
        "idx_objects_type_status",
        "objects",
        ["object_type_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_objects_owner_org",
        "objects",
        ["owner_org_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_objects_operator_org", "objects", ["operator_org_id"])
    op.create_index("idx_objects_maintainer_org", "objects", ["maintainer_org_id"])
    op.create_index("idx_objects_deployed_location", "objects", ["deployed_location_id"])
    op.create_index("idx_objects_created_by", "objects", ["created_by"])
    op.create_index("idx_objects_updated_by", "objects", ["updated_by"])
    op.create_index(
        "idx_objects_serial",
        "objects",
        ["serial_number"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_objects_firmware",
        "objects",
        ["firmware_version"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    _active_index("objects")

    op.create_table(
        "object_specs",
        _id(),
        sa.Column("object_id", UUID, nullable=False),
        sa.Column("spec_data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("data_source", sa.String(100), nullable=False),
        sa.Column("confidence", sa.String(50), nullable=False),
        sa.Column("data_status", sa.String(50), nullable=False),
        sa.Column("operator_id", UUID, nullable=True),
        sa.Column("last_successful_update", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        *_soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.CheckConstraint(
            "data_source IN ('DISCOVERY', 'MANUAL', 'IMPORT', 'DOCUMENT', "
            "'CUSTOMER_REPORT', 'VENDOR')",
            name="ck_object_specs_data_source",
        ),
        sa.CheckConstraint(
            "confidence IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_object_specs_confidence",
        ),
        sa.CheckConstraint(
            "data_status IN ('FRESH', 'NORMAL', 'STALE', 'UNKNOWN', 'INVALID')",
            name="ck_object_specs_data_status",
        ),
    )
    op.create_index(
        "idx_object_specs_object",
        "object_specs",
        ["object_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_object_specs_data", "object_specs", ["spec_data"], postgresql_using="gin")
    op.create_index(
        "idx_object_specs_status",
        "object_specs",
        ["data_status", "last_successful_update"],
    )
    op.create_index("idx_object_specs_operator", "object_specs", ["operator_id"])
    _active_index("object_specs")

    op.create_table(
        "relationships",
        _id(),
        sa.Column("source_object_id", UUID, nullable=False),
        sa.Column("relation_type_id", UUID, nullable=False),
        sa.Column("target_object_id", UUID, nullable=False),
        sa.Column("attributes", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("confidence", sa.String(50), nullable=False),
        sa.Column("data_source", sa.String(100), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by", UUID, nullable=True),
        *_soft_delete(),
        *_timestamps(),
        sa.Column("created_by", UUID, nullable=True),
        sa.ForeignKeyConstraint(["source_object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["relation_type_id"], ["relationship_types.id"]),
        sa.ForeignKeyConstraint(["target_object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'REMOVED')",
            name="ck_relationships_status",
        ),
        sa.CheckConstraint(
            "confidence IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_relationships_confidence",
        ),
    )
    op.create_index(
        "idx_relationships_source",
        "relationships",
        ["source_object_id", "relation_type_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_relationships_target",
        "relationships",
        ["target_object_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_relationships_type",
        "relationships",
        ["relation_type_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_relationships_verified_by", "relationships", ["verified_by"])
    op.create_index("idx_relationships_created_by", "relationships", ["created_by"])
    _active_index("relationships")

    op.create_table(
        "object_history",
        _id(),
        sa.Column("object_id", UUID, nullable=False),
        sa.Column("change_type", sa.String(100), nullable=False),
        sa.Column("before_data", JSONB, nullable=True),
        sa.Column("after_data", JSONB, nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("confidence", sa.String(50), nullable=True),
        sa.Column("operator", UUID, nullable=True),
        *_soft_delete(),
        *_timestamps(updated=False),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["operator"], ["users.id"]),
        sa.CheckConstraint(
            "change_type IN ('CREATE', 'UPDATE', 'DELETE', 'STATUS_CHANGE', 'LOCATION_CHANGE')",
            name="ck_object_history_change_type",
        ),
        sa.CheckConstraint(
            "source IN ('DISCOVERY', 'MANUAL', 'IMPORT', 'API')",
            name="ck_object_history_source",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_object_history_confidence",
        ),
    )
    op.create_index(
        "idx_object_history_object", "object_history", ["object_id", sa.text("created_at DESC")]
    )
    op.create_index(
        "idx_object_history_time",
        "object_history",
        ["created_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_object_history_operator", "object_history", ["operator"])
    _active_index("object_history")

    op.create_table(
        "user_roles",
        _id(),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("role_id", UUID, nullable=False),
        sa.Column("granted_by", UUID, nullable=True),
        sa.Column("granted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        *_soft_delete(),
        *_timestamps(updated=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("idx_user_roles_user", "user_roles", ["user_id"])
    op.create_index("idx_user_roles_role", "user_roles", ["role_id"])
    op.create_index("idx_user_roles_granted_by", "user_roles", ["granted_by"])
    _active_index("user_roles")

    op.create_table(
        "role_permissions",
        _id(),
        sa.Column("role_id", UUID, nullable=False),
        sa.Column("permission_id", UUID, nullable=False),
        *_soft_delete(),
        *_timestamps(updated=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    )
    op.create_index("idx_role_permissions_role", "role_permissions", ["role_id"])
    op.create_index("idx_role_permissions_permission", "role_permissions", ["permission_id"])
    _active_index("role_permissions")

    op.create_table(
        "audit_logs",
        _id(),
        sa.Column("user_id", UUID, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", UUID, nullable=True),
        sa.Column("before_data", JSONB, nullable=True),
        sa.Column("after_data", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        *_soft_delete(),
        *_timestamps(updated=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id", sa.text("created_at DESC")])
    op.create_index(
        "idx_audit_logs_resource",
        "audit_logs",
        ["resource_type", "resource_id", sa.text("created_at DESC")],
    )
    op.create_index("idx_audit_logs_action", "audit_logs", ["action", sa.text("created_at DESC")])
    op.create_index("idx_audit_logs_time", "audit_logs", [sa.text("created_at DESC")])
    _active_index("audit_logs")

    op.create_table(
        "idempotency_keys",
        _id(),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", JSONB, nullable=True),
        sa.Column("user_id", UUID, nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        *_soft_delete(),
        *_timestamps(updated=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("idx_idempotency_keys_key", "idempotency_keys", ["idempotency_key"])
    op.create_index("idx_idempotency_keys_expires", "idempotency_keys", ["expires_at"])
    op.create_index("idx_idempotency_keys_user", "idempotency_keys", ["user_id"])
    _active_index("idempotency_keys")


def downgrade() -> None:
    for table in (
        "idempotency_keys",
        "audit_logs",
        "role_permissions",
        "user_roles",
        "object_history",
        "relationships",
        "object_specs",
        "objects",
        "relationship_types",
        "object_types",
        "permissions",
        "roles",
        "users",
        "organizations",
    ):
        op.drop_table(table)
