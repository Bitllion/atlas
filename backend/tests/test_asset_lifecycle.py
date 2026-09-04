"""Asset transfer, retirement, and retirement-recovery integration tests."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import InventoryRecord, ObjectHistory, Organization, User


@pytest.fixture(scope="module")
def lifecycle_context():
    marker = uuid4().hex
    with SessionLocal() as db:
        source = Organization(name=f"lifecycle-source-{marker}", org_type="INTERNAL")
        target = Organization(name=f"lifecycle-target-{marker}", org_type="CUSTOMER")
        db.add_all([source, target])
        db.flush()
        user = User(username=f"lifecycle-{marker}", email=f"lifecycle-{marker}@example.test",
                    password_hash="test", organization_id=source.id)
        db.add(user)
        db.commit()
        return {"headers": {"X-User-Id": str(user.id)}, "target_org_id": str(target.id)}


def _new_stock_asset(client, type_ids, context, marker):
    headers = context["headers"]
    purchase = client.post("/api/v1/purchase-requests", json={
        "title": f"lifecycle-{marker}",
        "items": [{"object_type_id": type_ids["SERVER"], "quantity": 1, "model": "GB300"}],
    }, headers=headers)
    assert purchase.status_code == 201, purchase.text
    approved = client.post(f"/api/v1/purchase-requests/{purchase.json()['id']}/approve",
                           json={}, headers=headers)
    assert approved.status_code == 200, approved.text
    received = client.post("/api/v1/assets", json={
        "asset_number": f"LIFE-{marker}", "purchase_request_id": purchase.json()["id"],
        "object_type_id": type_ids["SERVER"], "name": f"lifecycle-server-{marker}",
    }, headers=headers)
    assert received.status_code == 201, received.text
    location = client.post("/api/v1/inventory-locations", json={
        "name": f"lifecycle-location-{marker}", "warehouse": "WH-LIFE",
        "location_code": f"LIFE-LOC-{marker}",
    })
    assert location.status_code == 201, location.text
    stocked = client.put(f"/api/v1/assets/{received.json()['id']}/stock",
                         json={"inventory_location_id": location.json()["id"]}, headers=headers)
    assert stocked.status_code == 200, stocked.text
    return stocked.json(), location.json()


def test_active_asset_transfer_complete_and_redeploy(client, type_ids, lifecycle_context):
    marker = uuid4().hex
    asset, _ = _new_stock_asset(client, type_ids, lifecycle_context, marker)
    rack = client.post("/api/v1/objects", json={
        "object_type_id": type_ids["RACK"], "name": f"transfer-rack-{marker}",
    })
    deployed = client.put(f"/api/v1/assets/{asset['id']}/deploy",
                          json={"location_id": rack.json()["id"]}, headers=lifecycle_context["headers"])
    assert deployed.status_code == 200, deployed.text

    transferred = client.put(f"/api/v1/assets/{asset['id']}/transfer", json={
        "target_organization_id": lifecycle_context["target_org_id"], "notes": "转移至客户库存",
    }, headers=lifecycle_context["headers"])
    assert transferred.status_code == 200, transferred.text
    assert transferred.json()["lifecycle_status"] == "TRANSFERRED"
    assert transferred.json()["operator_org_id"] == lifecycle_context["target_org_id"]

    destination = client.post("/api/v1/inventory-locations", json={
        "name": f"destination-{marker}", "warehouse": "WH-B",
        "location_code": f"DEST-{marker}",
    }).json()
    completed = client.put(f"/api/v1/assets/{asset['id']}/complete-transfer",
                           json={"inventory_location_id": destination["id"]},
                           headers=lifecycle_context["headers"])
    assert completed.status_code == 200, completed.text
    assert completed.json()["lifecycle_status"] == "STOCK"
    redeployed = client.put(f"/api/v1/assets/{asset['id']}/deploy", json={
        "location_id": rack.json()["id"], "deployment_type": "TRANSFER",
    }, headers=lifecycle_context["headers"])
    assert redeployed.status_code == 200, redeployed.text
    assert redeployed.json()["lifecycle_status"] == "ACTIVE"

    with SessionLocal() as db:
        records = db.scalars(select(InventoryRecord).where(InventoryRecord.asset_id == asset["id"])
                             .order_by(InventoryRecord.created_at)).all()
        assert [record.transaction_type for record in records][-2:] == ["IN", "OUT"]


def test_stock_retire_recover_and_restock(client, type_ids, lifecycle_context):
    marker = uuid4().hex
    asset, location = _new_stock_asset(client, type_ids, lifecycle_context, marker)
    retired = client.put(f"/api/v1/assets/{asset['id']}/retire", json={
        "reason": "设备达到报废标准", "disposition": "RMA",
    }, headers=lifecycle_context["headers"])
    assert retired.status_code == 200, retired.text
    assert retired.json()["lifecycle_status"] == "RETIRED"
    assert retired.json()["object"]["status"] == "RETIRED"

    invalid = client.put(f"/api/v1/assets/{asset['id']}/deploy",
                         json={"location_id": asset["object_id"]}, headers=lifecycle_context["headers"])
    assert invalid.status_code == 409
    assert invalid.json() == {"code": "InvalidAssetTransition", "message": "资产状态 RETIRED 不能转换为 DEPLOYED"}

    recovered = client.put(f"/api/v1/assets/{asset['id']}/recover",
                           json={"reason": "现场重新发现，确认误退役"}, headers=lifecycle_context["headers"])
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["lifecycle_status"] == "RECOVERED"
    assert recovered.json()["object"]["status"] == "MAINTENANCE"
    restocked = client.put(f"/api/v1/assets/{asset['id']}/complete-transfer",
                           json={"inventory_location_id": location["id"]}, headers=lifecycle_context["headers"])
    assert restocked.status_code == 200, restocked.text
    assert restocked.json()["lifecycle_status"] == "STOCK"

    timeline = client.get(f"/api/v1/assets/{asset['id']}/lifecycle").json()["items"]
    statuses = [event["event_type"] for event in timeline]
    assert statuses[-4:] == ["STOCK", "RETIRED", "RECOVERED", "STOCK"]
    with SessionLocal() as db:
        retirement = db.scalar(select(ObjectHistory).where(
            ObjectHistory.object_id == asset["object_id"],
            ObjectHistory.after_data["lifecycle_status"].astext == "RETIRED",
        ))
        assert retirement.after_data["reason"] == "设备达到报废标准"
        assert retirement.after_data["disposition"] == "RMA"
