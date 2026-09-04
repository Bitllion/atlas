"""Fine-grained role permission integration tests."""

from uuid import uuid4

from app.core.security import create_access_token
from app.database.session import SessionLocal
from app.models import Organization, Role, User, UserRole


def _create_user(role_name: str | None) -> User:
    suffix = uuid4().hex
    with SessionLocal.begin() as db:
        organization = Organization(name=f"RBAC Organization {suffix}", org_type="INTERNAL")
        db.add(organization)
        db.flush()
        user = User(
            username=f"rbac-{suffix}",
            email=f"rbac-{suffix}@example.test",
            password_hash="test-only",
            organization_id=organization.id,
        )
        db.add(user)
        db.flush()
        if role_name is not None:
            role = db.query(Role).filter(Role.name == role_name).one()
            db.add(UserRole(user_id=user.id, role_id=role.id, granted_by=user.id))
        db.flush()
        db.expunge(user)
        return user


def _bearer(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def test_viewer_can_read_objects_but_cannot_write_or_manage_users(unauthenticated_client):
    viewer = _create_user("viewer")
    headers = _bearer(viewer)

    assert unauthenticated_client.get("/api/v1/objects", headers=headers).status_code == 200

    write_response = unauthenticated_client.post("/api/v1/objects", headers=headers, json={})
    assert write_response.status_code == 403
    assert write_response.json()["code"] == "Forbidden"

    admin_response = unauthenticated_client.get("/api/v1/users", headers=headers)
    assert admin_response.status_code == 403
    assert admin_response.json()["code"] == "Forbidden"


def test_user_without_role_is_forbidden(unauthenticated_client):
    user = _create_user(None)
    response = unauthenticated_client.get("/api/v1/objects", headers=_bearer(user))
    assert response.status_code == 403
    assert response.json()["code"] == "Forbidden"


def test_admin_has_read_write_and_management_permissions(unauthenticated_client):
    admin = _create_user("admin")
    headers = _bearer(admin)

    assert unauthenticated_client.get("/api/v1/objects", headers=headers).status_code == 200
    # Permission evaluation happens before body validation, so 422 proves write access passed.
    assert unauthenticated_client.post("/api/v1/objects", headers=headers, json={}).status_code == 422
    assert unauthenticated_client.get("/api/v1/users", headers=headers).status_code == 200
