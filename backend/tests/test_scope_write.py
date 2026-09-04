"""Organization write isolation and dashboard aggregate integration tests."""

from uuid import uuid4

from sqlalchemy import func, select

from app.core.security import create_access_token
from app.database.session import SessionLocal
from app.models import Asset, InfrastructureObject, Organization, Role, User, UserRole
from app.services.resource_scope import organization_scope


def _bearer(user_id) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def test_object_writes_and_dashboard_are_organization_scoped(unauthenticated_client, type_ids):
    marker = uuid4().hex
    with SessionLocal.begin() as db:
        org_a = Organization(name=f"Write Scope A {marker}", org_type="INTERNAL")
        org_b = Organization(name=f"Write Scope B {marker}", org_type="CUSTOMER")
        db.add_all([org_a, org_b])
        db.flush()

        operator_role = db.query(Role).filter(Role.name == "operator").one()
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        user_b = User(
            username=f"write-scope-b-{marker}", email=f"write-scope-b-{marker}@example.test",
            password_hash="test-only", organization_id=org_b.id,
        )
        admin = User(
            username=f"write-scope-admin-{marker}", email=f"write-scope-admin-{marker}@example.test",
            password_hash="test-only", organization_id=org_b.id,
        )
        db.add_all([user_b, admin])
        db.flush()
        db.add_all([
            UserRole(user_id=user_b.id, role_id=operator_role.id, granted_by=user_b.id),
            UserRole(user_id=admin.id, role_id=admin_role.id, granted_by=admin.id),
        ])

        object_a = InfrastructureObject(
            object_type_id=type_ids["SERVER"], name=f"write-a-{marker}", status="ACTIVE",
            ownership="OWNED", management_scope="FULL_CONTROL", owner_org_id=org_a.id,
        )
        shared = InfrastructureObject(
            object_type_id=type_ids["SERVER"], name=f"write-shared-{marker}", status="ACTIVE",
            ownership="OWNED", management_scope="FULL_CONTROL",
        )
        db.add_all([object_a, shared])
        db.flush()
        for label, obj, owner in (("a", object_a, org_a.id), ("shared", shared, None)):
            db.add(Asset(
                object_id=obj.id, asset_number=f"WRITE-SCOPE-{marker}-{label}",
                lifecycle_status="ACTIVE", owner_org_id=owner,
            ))

    headers_b = _bearer(user_b.id)
    created = unauthenticated_client.post(
        "/api/v1/objects",
        json={"object_type_id": type_ids["SERVER"], "name": f"write-b-{marker}"},
        headers=headers_b,
    )
    assert created.status_code == 201, created.text
    assert created.json()["owner_org_id"] == str(org_b.id)
    assert created.json()["operator_org_id"] == str(org_b.id)

    forbidden_create = unauthenticated_client.post(
        "/api/v1/objects",
        json={
            "object_type_id": type_ids["SERVER"], "name": f"write-forbidden-{marker}",
            "owner_org_id": str(org_a.id),
        },
        headers=headers_b,
    )
    assert forbidden_create.status_code == 403
    assert forbidden_create.json()["code"] == "Forbidden"

    forbidden_update = unauthenticated_client.put(
        f"/api/v1/objects/{object_a.id}", json={"version": 1, "name": f"blocked-{marker}"},
        headers=headers_b,
    )
    assert forbidden_update.status_code == 403
    assert forbidden_update.json()["code"] == "Forbidden"

    shared_update = unauthenticated_client.put(
        f"/api/v1/objects/{shared.id}", json={"version": 1, "name": f"shared-updated-{marker}"},
        headers=headers_b,
    )
    assert shared_update.status_code == 200, shared_update.text

    with SessionLocal() as db:
        expected_b_objects = db.scalar(
            select(func.count()).select_from(InfrastructureObject).where(
                InfrastructureObject.deleted_at.is_(None),
                organization_scope(InfrastructureObject, org_b.id),
            )
        )
        expected_b_assets = db.scalar(
            select(func.count()).select_from(Asset).where(
                Asset.deleted_at.is_(None), organization_scope(Asset, org_b.id),
            )
        )
        expected_all_objects = db.scalar(
            select(func.count()).select_from(InfrastructureObject).where(InfrastructureObject.deleted_at.is_(None))
        )
        expected_all_assets = db.scalar(
            select(func.count()).select_from(Asset).where(Asset.deleted_at.is_(None))
        )

    scoped_dashboard = unauthenticated_client.get("/api/v1/dashboard/overview", headers=headers_b)
    assert scoped_dashboard.status_code == 200, scoped_dashboard.text
    assert scoped_dashboard.json()["devices"]["total"] == expected_b_objects
    assert scoped_dashboard.json()["assets"]["total"] == expected_b_assets

    admin_dashboard = unauthenticated_client.get(
        "/api/v1/dashboard/overview", headers=_bearer(admin.id)
    )
    assert admin_dashboard.status_code == 200, admin_dashboard.text
    assert admin_dashboard.json()["devices"]["total"] == expected_all_objects
    assert admin_dashboard.json()["assets"]["total"] == expected_all_assets
