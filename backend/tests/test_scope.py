"""Organization resource-scope integration tests for core read lists."""

from uuid import uuid4

from app.core.security import create_access_token
from app.database.session import SessionLocal
from app.models import Asset, InfrastructureObject, Organization, Role, User, UserRole


def _bearer(user_id) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def test_object_and_asset_lists_are_organization_scoped(unauthenticated_client, type_ids):
    marker = uuid4().hex
    with SessionLocal.begin() as db:
        org_a = Organization(name=f"Scope A {marker}", org_type="INTERNAL")
        org_b = Organization(name=f"Scope B {marker}", org_type="CUSTOMER")
        db.add_all([org_a, org_b])
        db.flush()

        operator_role = db.query(Role).filter(Role.name == "operator").one()
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        users = []
        for label, organization, role in (
            ("a", org_a, operator_role),
            ("b", org_b, operator_role),
            ("admin", org_b, admin_role),
        ):
            user = User(
                username=f"scope-{label}-{marker}",
                email=f"scope-{label}-{marker}@example.test",
                password_hash="test-only",
                organization_id=organization.id,
            )
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id, granted_by=user.id))
            users.append(user.id)

        location = InfrastructureObject(
            object_type_id=type_ids["RACK"], name=f"scope-location-{marker}",
            status="ACTIVE", ownership="OWNED", management_scope="FULL_CONTROL",
            owner_org_id=org_a.id,
        )
        db.add(location)
        db.flush()
        objects = []
        for label, owner_org_id, operator_org_id in (
            ("a", org_a.id, None),
            ("b", org_b.id, None),
            ("shared", None, None),
        ):
            obj = InfrastructureObject(
                object_type_id=type_ids["SERVER"], name=f"scope-object-{marker}-{label}",
                status="ACTIVE", ownership="OWNED", management_scope="FULL_CONTROL",
                owner_org_id=owner_org_id, operator_org_id=operator_org_id,
                deployed_location_id=location.id,
            )
            db.add(obj)
            db.flush()
            db.add(Asset(
                object_id=obj.id, asset_number=f"SCOPE-ASSET-{marker}-{label}",
                lifecycle_status="ACTIVE", owner_org_id=owner_org_id,
                operator_org_id=operator_org_id,
            ))
            objects.append(obj.id)

    user_a_id, user_b_id, admin_id = users
    object_params = {"name": f"scope-object-{marker}", "page_size": 1}
    a_objects = unauthenticated_client.get("/api/v1/objects", params=object_params, headers=_bearer(user_a_id)).json()
    assert a_objects["total"] == 2
    assert len(a_objects["items"]) == 1
    a_all_objects = unauthenticated_client.get("/api/v1/objects", params={**object_params, "page_size": 20}, headers=_bearer(user_a_id)).json()
    assert {item["id"] for item in a_all_objects["items"]} == {str(objects[0]), str(objects[2])}

    b_objects = unauthenticated_client.get("/api/v1/objects", params={**object_params, "page_size": 20}, headers=_bearer(user_b_id)).json()
    assert {item["id"] for item in b_objects["items"]} == {str(objects[1]), str(objects[2])}
    admin_objects = unauthenticated_client.get("/api/v1/objects", params={**object_params, "page_size": 20}, headers=_bearer(admin_id)).json()
    assert admin_objects["total"] == 3

    asset_params = {"location_id": str(location.id), "page_size": 20}
    a_assets = unauthenticated_client.get("/api/v1/assets", params=asset_params, headers=_bearer(user_a_id)).json()
    assert a_assets["total"] == 2
    assert {item["object_id"] for item in a_assets["items"]} == {str(objects[0]), str(objects[2])}
    admin_assets = unauthenticated_client.get("/api/v1/assets", params=asset_params, headers=_bearer(admin_id)).json()
    assert admin_assets["total"] == 3
