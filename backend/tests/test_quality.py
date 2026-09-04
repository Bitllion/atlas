"""Tests for data quality center endpoints."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import InfrastructureObject, ObjectSpec, ObjectType, Organization, User, UserRole


@pytest.fixture
def setup_quality_data():
    """Create test objects with various quality issues."""
    with SessionLocal.begin() as db:
        # Get a type
        server_type = db.scalar(select(ObjectType).where(ObjectType.name == "SERVER"))
        assert server_type is not None

        # Get test user and org
        test_user = db.scalar(select(User).where(User.username == "atlas-test-user"))
        assert test_user is not None
        test_org_id = test_user.organization_id

        # Create objects with different quality issues
        # 1. Object missing serial_number
        obj1 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Missing SN",
            serial_number=None,
            manufacturer="Dell",
            model="R740",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj1)

        # 2. Object missing manufacturer
        obj2 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Missing Manufacturer",
            serial_number="SN12345",
            manufacturer=None,
            model="R740",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj2)

        # 3. Object missing model
        obj3 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Missing Model",
            serial_number="SN67890",
            manufacturer="HP",
            model=None,
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj3)

        # 4. Object missing spec
        obj4 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Missing Spec",
            serial_number="SN11111",
            manufacturer="Lenovo",
            model="ThinkSystem",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj4)

        # 5. Object with STALE spec
        obj5 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Stale Spec",
            serial_number="SN22222",
            manufacturer="Dell",
            model="R750",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj5)
        db.flush()

        spec5 = ObjectSpec(
            object_id=obj5.id,
            spec_data={"cpu": "Intel Xeon"},
            data_source="DISCOVERY",
            confidence="HIGH",
            data_status="STALE",
        )
        db.add(spec5)

        # 6. Object with UNKNOWN spec status
        obj6 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Unknown Spec",
            serial_number="SN33333",
            manufacturer="HP",
            model="ProLiant",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj6)
        db.flush()

        spec6 = ObjectSpec(
            object_id=obj6.id,
            spec_data={"cpu": "AMD EPYC"},
            data_source="MANUAL",
            confidence="MEDIUM",
            data_status="UNKNOWN",
        )
        db.add(spec6)

        # 7. Object with LOW confidence spec
        obj7 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Server Low Confidence",
            serial_number="SN44444",
            manufacturer="Dell",
            model="R740xd",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=test_org_id,
            operator_org_id=test_org_id,
        )
        db.add(obj7)
        db.flush()

        spec7 = ObjectSpec(
            object_id=obj7.id,
            spec_data={"cpu": "Unknown"},
            data_source="IMPORT",
            confidence="LOW",
            data_status="NORMAL",
        )
        db.add(spec7)

        # 8. Unattributed object (no owner/operator org)
        obj8 = InfrastructureObject(
            object_type_id=server_type.id,
            name="Unattributed Server",
            serial_number="SN55555",
            manufacturer="Cisco",
            model="UCS",
            status="ACTIVE",
            ownership="OWNED",
            management_scope="FULL_CONTROL",
            owner_org_id=None,
            operator_org_id=None,
        )
        db.add(obj8)

    yield

    # Cleanup
    with SessionLocal.begin() as db:
        db.query(ObjectSpec).filter(ObjectSpec.object_id.in_([
            obj5.id, obj6.id, obj7.id
        ])).delete(synchronize_session=False)
        db.query(InfrastructureObject).filter(InfrastructureObject.name.like("Server %")).delete(synchronize_session=False)
        db.query(InfrastructureObject).filter(InfrastructureObject.name == "Unattributed Server").delete(synchronize_session=False)


def test_quality_overview(client: TestClient, setup_quality_data):
    """Test quality overview aggregation by type."""
    response = client.get("/api/v1/quality/overview")
    assert response.status_code == 200

    data = response.json()
    assert "by_type" in data
    assert len(data["by_type"]) > 0

    # Find server type in results
    server_stats = next((item for item in data["by_type"] if item["object_type"] == "SERVER"), None)
    assert server_stats is not None

    # Verify we have at least our test objects
    assert server_stats["total"] >= 7
    assert server_stats["missing_serial_number"] >= 1
    assert server_stats["missing_manufacturer"] >= 1
    assert server_stats["missing_model"] >= 1
    assert server_stats["missing_spec"] >= 1
    assert server_stats["spec_status"]["stale"] >= 1
    assert server_stats["spec_status"]["unknown"] >= 1
    assert server_stats["low_confidence"] >= 1


def test_quality_details_no_filter(client: TestClient, setup_quality_data):
    """Test details endpoint without filters."""
    response = client.get("/api/v1/quality/details")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 7

    # Verify structure
    if data["items"]:
        item = data["items"][0]
        assert "id" in item
        assert "name" in item
        assert "object_type" in item
        assert "missing_fields" in item
        assert isinstance(item["missing_fields"], list)


def test_quality_details_filter_by_type(client: TestClient, setup_quality_data):
    """Test filtering by object type."""
    response = client.get("/api/v1/quality/details?type=SERVER")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 7

    # All items should be servers
    for item in data["items"]:
        assert item["object_type"] == "SERVER"


def test_quality_details_filter_missing_serial(client: TestClient, setup_quality_data):
    """Test filtering by missing serial_number."""
    response = client.get("/api/v1/quality/details?missing=serial_number")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1

    # All items should have serial_number in missing_fields
    for item in data["items"]:
        assert "serial_number" in item["missing_fields"]


def test_quality_details_filter_missing_manufacturer(client: TestClient, setup_quality_data):
    """Test filtering by missing manufacturer."""
    response = client.get("/api/v1/quality/details?missing=manufacturer")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1

    for item in data["items"]:
        assert "manufacturer" in item["missing_fields"]


def test_quality_details_filter_missing_model(client: TestClient, setup_quality_data):
    """Test filtering by missing model."""
    response = client.get("/api/v1/quality/details?missing=model")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1

    for item in data["items"]:
        assert "model" in item["missing_fields"]


def test_quality_details_filter_missing_spec(client: TestClient, setup_quality_data):
    """Test filtering by missing spec."""
    response = client.get("/api/v1/quality/details?missing=spec")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1

    for item in data["items"]:
        assert "spec" in item["missing_fields"]


def test_quality_details_pagination(client: TestClient, setup_quality_data):
    """Test pagination of details endpoint."""
    response = client.get("/api/v1/quality/details?page=1&page_size=3")
    assert response.status_code == 200

    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) <= 3


def test_quality_unattributed(client: TestClient, setup_quality_data):
    """Test unattributed objects endpoint."""
    response = client.get("/api/v1/quality/unattributed")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1

    # Find our unattributed server
    unattributed = next((item for item in data["items"] if item["name"] == "Unattributed Server"), None)
    assert unattributed is not None
    assert unattributed["serial_number"] == "SN55555"
    assert unattributed["object_type"] == "SERVER"


def test_quality_unattributed_pagination(client: TestClient, setup_quality_data):
    """Test pagination of unattributed endpoint."""
    response = client.get("/api/v1/quality/unattributed?page=1&page_size=5")
    assert response.status_code == 200

    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5


def test_quality_organization_isolation(client: TestClient, setup_quality_data):
    """Test that non-admin users only see their organization's data."""
    with SessionLocal.begin() as db:
        # Create a different organization and user
        other_org = Organization(name="Other Org", org_type="CUSTOMER")
        db.add(other_org)
        db.flush()

        other_user = User(
            username="other-user",
            email="other@example.test",
            password_hash="test",
            organization_id=other_org.id,
        )
        db.add(other_user)
        db.flush()

        # Give them viewer role (has quality.read)
        from app.models import Role
        viewer_role = db.scalar(select(Role).where(Role.name == "viewer"))
        assert viewer_role is not None
        db.add(UserRole(user_id=other_user.id, role_id=viewer_role.id, granted_by=other_user.id))

        other_user_id = str(other_user.id)

    # Get counts as test org user (admin - sees all)
    admin_response = client.get("/api/v1/quality/overview")
    assert admin_response.status_code == 200
    admin_data = admin_response.json()
    admin_server_stats = next((item for item in admin_data["by_type"] if item["object_type"] == "SERVER"), None)
    admin_total = admin_server_stats["total"] if admin_server_stats else 0

    # Make request as the other user (non-admin)
    other_client = TestClient(client.app, headers={"X-User-Id": other_user_id})
    response = other_client.get("/api/v1/quality/overview")
    assert response.status_code == 200

    data = response.json()
    # Other user should see fewer objects than admin (only shared/unattributed)
    other_server_stats = next((item for item in data["by_type"] if item["object_type"] == "SERVER"), None)

    # Should see at least the unattributed server, but fewer than admin total
    if other_server_stats:
        # Should NOT see all objects (admin sees test org objects + shared)
        # Other user only sees shared/unattributed
        assert other_server_stats["total"] < admin_total

    # Cleanup
    with SessionLocal.begin() as db:
        db.query(UserRole).filter(UserRole.user_id == UUID(other_user_id)).delete()
        db.query(User).filter(User.id == UUID(other_user_id)).delete()
        db.query(Organization).filter(Organization.name == "Other Org").delete()
