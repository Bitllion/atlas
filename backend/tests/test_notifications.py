"""In-app notification API and business-trigger integration tests."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Organization, Role, User, UserRole


@pytest.fixture(scope="module")
def notification_user():
    marker = uuid4().hex
    with SessionLocal.begin() as db:
        organization = Organization(name=f"notification-{marker}", org_type="INTERNAL")
        db.add(organization)
        db.flush()
        user = User(
            username=f"notification-{marker}", email=f"notification-{marker}@example.test",
            password_hash="test", organization_id=organization.id,
        )
        db.add(user)
        db.flush()
        operator = db.scalar(select(Role).where(Role.name == "operator"))
        assert operator is not None
        db.add(UserRole(user_id=user.id, role_id=operator.id))
        result = {"id": str(user.id), "headers": {"X-User-Id": str(user.id)}}
    return result


def test_work_order_assignment_unread_count_and_mark_read(client, type_ids, notification_user):
    object_response = client.post("/api/v1/objects", json={
        "object_type_id": type_ids["SERVER"], "name": f"notification-server-{uuid4().hex}",
        "status": "ACTIVE",
    })
    assert object_response.status_code == 201, object_response.text
    created = client.post("/api/v1/work-orders", json={
        "title": "通知派单测试", "type": "FAULT", "priority": "HIGH",
        "object_id": object_response.json()["id"],
    })
    assert created.status_code == 201, created.text
    assigned = client.put(f"/api/v1/work-orders/{created.json()['id']}/assign", json={
        "assignee_id": notification_user["id"],
    })
    assert assigned.status_code == 200, assigned.text

    unread = client.get("/api/v1/notifications/my/unread-count", headers=notification_user["headers"])
    assert unread.status_code == 200
    assert unread.json()["count"] == 1
    listing = client.get("/api/v1/notifications/my", headers=notification_user["headers"])
    assert listing.status_code == 200
    item = listing.json()["items"][0]
    assert item["type"] == "WORK_ORDER_ASSIGNED"
    assert item["entity_id"] == created.json()["id"]
    assert created.json()["work_order_number"] in item["message"]

    marked = client.put(f"/api/v1/notifications/{item['id']}/read", headers=notification_user["headers"])
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
    assert marked.json()["read_at"] is not None
    assert client.get("/api/v1/notifications/my/unread-count", headers=notification_user["headers"]).json() == {"count": 0}


def test_workflow_task_creation_notifies_assignee(client, notification_user):
    marker = uuid4().hex
    definition = client.post("/api/v1/workflow/definitions", json={
        "name": f"通知审批流-{marker}", "code": f"NOTIFICATION_{marker}",
        "definition": {
            "nodes": [
                {"id": "approve", "type": "approval", "assignee_user_id": notification_user["id"]},
                {"id": "end", "type": "end"},
            ],
            "edges": [{"source": "approve", "target": "end"}],
        },
    })
    assert definition.status_code == 201, definition.text
    entity_id = str(uuid4())
    business_key = f"PR-{marker[:8]}"
    started = client.post("/api/v1/workflow/instances", json={
        "definition_code": definition.json()["code"], "entity_type": "PURCHASE_REQUEST",
        "entity_id": entity_id, "business_key": business_key,
    })
    assert started.status_code == 201, started.text

    listing = client.get("/api/v1/notifications/my", headers=notification_user["headers"])
    task_notification = next(
        item for item in listing.json()["items"]
        if item["type"] == "WORKFLOW_TASK" and item["entity_id"] == entity_id
    )
    assert task_notification["message"] == f"有新的审批任务:采购单 {business_key}"


def test_notification_is_private_and_read_all(client, notification_user):
    own = client.get("/api/v1/notifications/my", headers=notification_user["headers"]).json()["items"]
    unread = next(item for item in own if not item["is_read"])
    assert client.put(f"/api/v1/notifications/{unread['id']}/read").status_code == 404
    response = client.put("/api/v1/notifications/read-all", headers=notification_user["headers"])
    assert response.status_code == 200
    assert response.json()["updated"] >= 1
    assert client.get("/api/v1/notifications/my/unread-count", headers=notification_user["headers"]).json() == {"count": 0}
