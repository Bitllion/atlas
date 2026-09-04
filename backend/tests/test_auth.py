"""Authentication, password, JWT, and compatibility-mode integration tests."""

from uuid import uuid4

import pytest

from app.config.settings import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import Organization, Role, User, UserRole


PASSWORD = "auth-test-password"


@pytest.fixture(scope="module")
def auth_user(test_database):
    marker = uuid4().hex
    with SessionLocal.begin() as db:
        organization = Organization(name=f"Auth Organization {marker}", org_type="INTERNAL")
        db.add(organization)
        db.flush()
        user = User(
            username=f"auth-user-{marker}",
            email=f"auth-{marker}@example.test",
            full_name="Auth Test User",
            password_hash=hash_password(PASSWORD),
            organization_id=organization.id,
        )
        role = Role(name=f"auth-role-{marker}", description="Authentication test role")
        db.add_all([user, role])
        db.flush()
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        db.add_all([
            UserRole(user_id=user.id, role_id=role.id, granted_by=user.id),
            UserRole(user_id=user.id, role_id=admin_role.id, granted_by=user.id),
        ])
        return {
            "id": str(user.id),
            "username": user.username,
            "organization_id": str(organization.id),
            "role": role.name,
        }


def _login(client, auth_user, password=PASSWORD):
    return client.post(
        "/api/v1/auth/login",
        json={"username": auth_user["username"], "password": password},
    )


def test_login_success_returns_token_user_and_roles(client, auth_user):
    response = _login(client, auth_user)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {
        "id": auth_user["id"],
        "username": auth_user["username"],
        "full_name": "Auth Test User",
        "organization_id": auth_user["organization_id"],
        "roles": ["admin", auth_user["role"]],
    }


def test_login_failure_has_standard_error(client, auth_user):
    response = _login(client, auth_user, "wrong-password")
    assert response.status_code == 401
    assert response.json() == {"code": "InvalidCredentials", "message": "用户名或密码错误"}


def test_me_with_bearer(client, auth_user):
    token = _login(client, auth_user).json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == auth_user["id"]


def test_change_password(client, auth_user):
    token = _login(client, auth_user).json()["access_token"]
    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": PASSWORD, "new_password": "changed-auth-password"},
    )
    assert response.status_code == 200
    assert _login(client, auth_user).status_code == 401
    assert _login(client, auth_user, "changed-auth-password").status_code == 200

    # Restore the fixture password so this test remains repeatable in any order.
    with SessionLocal.begin() as db:
        user = db.get(User, auth_user["id"])
        user.password_hash = hash_password(PASSWORD)


def test_dev_header_compatibility_and_bearer_priority(client, auth_user):
    original_mode = settings.auth_mode
    settings.auth_mode = "dev"
    try:
        header_response = client.post(
            "/api/v1/organizations",
            headers={"X-User-Id": auth_user["id"]},
            json={"name": f"Dev Header Org {uuid4().hex}", "org_type": "INTERNAL"},
        )
        assert header_response.status_code == 201

        token = _login(client, auth_user).json()["access_token"]
        bearer_response = client.post(
            "/api/v1/organizations",
            headers={
                "Authorization": f"Bearer {token}",
                "X-User-Id": str(uuid4()),
            },
            json={"name": f"Bearer Priority Org {uuid4().hex}", "org_type": "INTERNAL"},
        )
        assert bearer_response.status_code == 201
    finally:
        settings.auth_mode = original_mode


def test_no_credentials_and_prod_header_only_are_unauthorized(
    client, unauthenticated_client, auth_user
):
    payload = {"name": f"Unauthorized Org {uuid4().hex}", "org_type": "INTERNAL"}
    response = unauthenticated_client.post("/api/v1/organizations", json=payload)
    assert response.status_code == 401
    assert response.json()["code"] == "Unauthorized"

    original_mode = settings.auth_mode
    settings.auth_mode = "prod"
    try:
        response = client.post(
            "/api/v1/organizations",
            headers={"X-User-Id": auth_user["id"]},
            json=payload,
        )
        assert response.status_code == 401
    finally:
        settings.auth_mode = original_mode
