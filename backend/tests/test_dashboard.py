"""Phase 5a dashboard aggregation tests."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models import Asset, InfrastructureObject, WorkOrder

USER_ID = UUID("7c17910d-850b-4a4b-bf93-e556984edab3")


def _counts(items, key):
    return {item[key]: item["count"] for item in items}


def test_dashboard_statistics_are_correct(client, type_ids):
    before = client.get("/api/v1/dashboard/overview").json()
    marker = uuid4().hex
    now = datetime.now()
    with SessionLocal() as db:
        server = InfrastructureObject(object_type_id=UUID(type_ids["SERVER"]), name=f"dashboard-server-{marker}", serial_number=f"DASH-{marker}", status="ACTIVE", ownership="OWNED", management_scope="FULL_CONTROL", created_by=USER_ID)
        gpu = InfrastructureObject(object_type_id=UUID(type_ids["GPU"]), name=f"dashboard-gpu-{marker}", status="ACTIVE", ownership="OWNED", management_scope="FULL_CONTROL", created_by=USER_ID)
        db.add_all([server, gpu])
        db.flush()
        db.add_all([
            Asset(object_id=server.id, asset_number=f"DASH-A-{marker}", lifecycle_status="STOCK", created_by=USER_ID),
            Asset(object_id=gpu.id, asset_number=f"DASH-B-{marker}", lifecycle_status="ACTIVE", created_by=USER_ID),
            WorkOrder(work_order_number=f"DASH-OPEN-{marker}", title="dashboard open", type="FAULT", priority="HIGH", status="CREATED", related_object_id=gpu.id, created_by=USER_ID, created_at=now),
            WorkOrder(work_order_number=f"DASH-DONE-{marker}", title="dashboard resolved", type="REPAIR", priority="LOW", status="RESOLVED", related_object_id=server.id, created_by=USER_ID, created_at=now - timedelta(hours=4), resolved_at=now, resolved_by=USER_ID),
        ])
        db.commit()

    overview = client.get("/api/v1/dashboard/overview")
    assert overview.status_code == 200, overview.text
    data = overview.json()
    assert data["devices"]["total"] == before["devices"]["total"] + 2
    assert _counts(data["devices"]["by_type"], "type")["SERVER"] == _counts(before["devices"]["by_type"], "type").get("SERVER", 0) + 1
    assert _counts(data["assets"]["by_status"], "status")["STOCK"] == _counts(before["assets"]["by_status"], "status").get("STOCK", 0) + 1
    assert data["work_orders"]["total"] == before["work_orders"]["total"] + 2
    assert data["work_orders"]["open"] == before["work_orders"]["open"] + 1
    assert data["work_orders"]["resolved"] == before["work_orders"]["resolved"] + 1

    assets = client.get("/api/v1/dashboard/assets").json()
    assert assets["total"] == data["assets"]["total"]
    assert _counts(assets["by_type"], "type")["GPU"] >= 1
    operations = client.get("/api/v1/dashboard/operations").json()
    assert _counts(operations["by_status"], "status")["RESOLVED"] >= 1
    assert _counts(operations["by_priority"], "priority")["HIGH"] >= 1
    with SessionLocal() as db:
        expected = db.scalar(select(func.avg(func.extract("epoch", WorkOrder.resolved_at - WorkOrder.created_at)) / 3600).where(WorkOrder.deleted_at.is_(None), WorkOrder.resolved_at.is_not(None)))
    assert operations["average_repair_hours"] == round(float(expected), 2)
