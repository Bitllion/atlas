"""Purchase-request integration with the generic workflow engine."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Organization, PurchaseRequest, Role, User, UserRole


@pytest.fixture(scope="module")
def approval_users():
    marker = uuid4().hex
    with SessionLocal.begin() as db:
        organization = Organization(name=f"purchase-workflow-{marker}", org_type="INTERNAL")
        db.add(organization)
        db.flush()
        operator = User(username=f"operator-{marker}", email=f"operator-{marker}@example.test", password_hash="test", organization_id=organization.id)
        admin = User(username=f"admin-{marker}", email=f"admin-{marker}@example.test", password_hash="test", organization_id=organization.id)
        other_org = Organization(name=f"purchase-workflow-other-{marker}", org_type="CUSTOMER")
        db.add(other_org)
        db.flush()
        outsider = User(username=f"outsider-{marker}", email=f"outsider-{marker}@example.test", password_hash="test", organization_id=other_org.id)
        db.add_all((operator, admin, outsider))
        db.flush()
        roles = {role.name: role for role in db.scalars(select(Role).where(Role.name.in_(("operator", "admin"))))}
        db.add_all((
            UserRole(user_id=operator.id, role_id=roles["operator"].id),
            UserRole(user_id=admin.id, role_id=roles["admin"].id),
            UserRole(user_id=outsider.id, role_id=roles["operator"].id),
        ))
        result = {
            "operator": {"X-User-Id": str(operator.id)},
            "admin": {"X-User-Id": str(admin.id)},
            "outsider": {"X-User-Id": str(outsider.id)},
            "operator_id": str(operator.id),
            "admin_id": str(admin.id),
        }
    return result


def _create(client, type_ids, headers):
    response = client.post("/api/v1/purchase-requests", json={
        "title": f"采购服务器 {uuid4().hex}",
        "items": [{"object_type_id": type_ids["SERVER"], "quantity": 1, "model": "GB300"}],
        "currency": "CNY", "justification": "容量扩展",
    }, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_purchase_two_level_workflow_approval(client, type_ids, approval_users):
    purchase = _create(client, type_ids, approval_users["operator"])
    workflow = client.get(f"/api/v1/purchase-requests/{purchase['id']}/workflow", headers=approval_users["operator"])
    assert workflow.status_code == 200, workflow.text
    assert workflow.json()["status"] == "RUNNING"
    assert workflow.json()["business_key"] == purchase["request_number"]
    first = workflow.json()["current_tasks"]
    assert [(task["node_id"], task["assignee_id"]) for task in first] == [("n1", approval_users["operator_id"])]
    hidden = client.get(f"/api/v1/purchase-requests/{purchase['id']}/workflow", headers=approval_users["outsider"])
    assert hidden.status_code == 404
    listing = client.get("/api/v1/purchase-requests", headers=approval_users["outsider"])
    assert purchase["id"] not in {item["id"] for item in listing.json()["items"]}

    legacy = client.post(f"/api/v1/purchase-requests/{purchase['id']}/approve", json={}, headers=approval_users["operator"])
    assert legacy.status_code == 409
    assert legacy.json()["code"] == "PurchaseWorkflowActive"

    first_result = client.post(f"/api/v1/workflow/tasks/{first[0]['id']}/approve", json={"comment": "部门同意"}, headers=approval_users["operator"])
    assert first_result.status_code == 200, first_result.text
    assert first_result.json()["current_node_id"] == "n2"

    workflow = client.get(f"/api/v1/purchase-requests/{purchase['id']}/workflow", headers=approval_users["admin"]).json()
    second = workflow["current_tasks"]
    assert [(task["node_id"], task["assignee_id"]) for task in second] == [("n2", approval_users["admin_id"])]
    completed = client.post(f"/api/v1/workflow/tasks/{second[0]['id']}/approve", json={"comment": "采购终审通过"}, headers=approval_users["admin"])
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"

    with SessionLocal() as db:
        saved = db.get(PurchaseRequest, purchase["id"])
        assert saved.status == "APPROVED"
        assert str(saved.approved_by) == approval_users["admin_id"]
        assert saved.approved_at is not None


def test_purchase_workflow_rejection(client, type_ids, approval_users):
    purchase = _create(client, type_ids, approval_users["operator"])
    workflow = client.get(f"/api/v1/purchase-requests/{purchase['id']}/workflow", headers=approval_users["operator"]).json()
    rejected = client.post(
        f"/api/v1/workflow/tasks/{workflow['current_tasks'][0]['id']}/reject",
        json={"comment": "部门预算不足"}, headers=approval_users["operator"],
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "TERMINATED"
    with SessionLocal() as db:
        saved = db.get(PurchaseRequest, purchase["id"])
        assert saved.status == "REJECTED"
        assert str(saved.rejected_by) == approval_users["operator_id"]
        assert saved.rejection_reason == "部门预算不足"
