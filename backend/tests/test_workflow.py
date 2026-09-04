"""End-to-end tests for sequential workflow approvals."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models import Organization, Role, User, UserRole


def _definition(client, suffix: str, levels: int = 3) -> str:
    nodes = [
        {"id": f"n{i}", "type": "approval", "assignee_role": "admin"}
        for i in range(1, levels + 1)
    ] + [{"id": "end", "type": "end"}]
    edges = [
        {"source": nodes[i]["id"], "target": nodes[i + 1]["id"]}
        for i in range(len(nodes) - 1)
    ]
    response = client.post("/api/v1/workflow/definitions", json={
        "name": f"测试审批流-{suffix}", "code": f"TEST_{suffix}",
        "definition": {"nodes": nodes, "edges": edges},
    })
    assert response.status_code == 201, response.text
    return response.json()["code"]


def _start(client, code: str) -> dict:
    response = client.post("/api/v1/workflow/instances", json={
        "definition_code": code, "entity_type": "PURCHASE_REQUEST",
        "entity_id": str(uuid4()), "business_key": f"PR-{uuid4().hex[:8]}",
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_three_level_approval_and_my_tasks(client):
    instance = _start(client, _definition(client, uuid4().hex))
    assert instance["status"] == "RUNNING"
    assert instance["current_node_id"] == "n1"

    for level in range(1, 4):
        pending = client.get("/api/v1/workflow/tasks/my")
        assert pending.status_code == 200
        tasks = [item for item in pending.json()["items"] if item["instance_id"] == instance["id"]]
        assert len(tasks) == 1
        assert tasks[0]["node_id"] == f"n{level}"
        response = client.post(f"/api/v1/workflow/tasks/{tasks[0]['id']}/approve", json={"comment": f"level {level} ok"})
        assert response.status_code == 200, response.text
        instance = response.json()

    assert instance["status"] == "COMPLETED"
    assert instance["current_node_id"] is None
    detail = client.get(f"/api/v1/workflow/instances/{instance['id']}")
    assert detail.status_code == 200
    history = detail.json()["tasks"]
    assert [task["node_id"] for task in history if task["status"] == "APPROVED"] == ["n1", "n2", "n3"]
    assert all(task["status"] in {"APPROVED", "SKIPPED"} for task in history)


def test_reject_terminates_instance(client):
    instance = _start(client, _definition(client, uuid4().hex, levels=1))
    tasks = client.get("/api/v1/workflow/tasks/my").json()["items"]
    task = next(item for item in tasks if item["instance_id"] == instance["id"])
    response = client.post(f"/api/v1/workflow/tasks/{task['id']}/reject", json={"comment": "not approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "TERMINATED"
    detail = client.get(f"/api/v1/workflow/instances/{instance['id']}").json()
    rejected = next(task for task in detail["tasks"] if task["status"] == "REJECTED")
    assert rejected["comment"] == "not approved"


def test_workflow_permission_denied(test_database):
    with SessionLocal.begin() as db:
        organization = Organization(name=f"Viewer Org {uuid4()}", org_type="CUSTOMER")
        db.add(organization)
        db.flush()
        user = User(username=f"viewer-{uuid4()}", email=f"viewer-{uuid4()}@example.test", password_hash="test-only", organization_id=organization.id)
        db.add(user)
        db.flush()
        viewer = db.scalar(select(Role).where(Role.name == "viewer"))
        assert viewer is not None
        db.add(UserRole(user_id=user.id, role_id=viewer.id))
        user_id = user.id
    with TestClient(app, headers={"X-User-Id": str(user_id)}) as viewer_client:
        response = viewer_client.post("/api/v1/workflow/instances", json={
            "definition_code": "MISSING", "entity_type": "PURCHASE_REQUEST", "entity_id": str(uuid4()),
        })
    assert response.status_code == 403
    assert response.json() == {"code": "Forbidden", "message": "缺少权限：workflow.write"}
