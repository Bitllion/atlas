"""Phase 3a asset lifecycle integration tests."""

from uuid import uuid4

import pytest
from app.database.session import SessionLocal
from app.models import Organization, Role, User, UserRole


@pytest.fixture(scope="module")
def user_headers():
    marker = uuid4().hex
    with SessionLocal() as db:
        organization = Organization(name=f"asset-test-org-{marker}", org_type="INTERNAL")
        db.add(organization)
        db.flush()
        user = User(username=f"asset-user-{marker}", email=f"{marker}@example.test", password_hash="test", organization_id=organization.id)
        db.add(user)
        db.flush()
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        db.add(UserRole(user_id=user.id, role_id=admin_role.id, granted_by=user.id))
        db.commit()
        db.refresh(user)
        return {"X-User-Id": str(user.id)}


def _purchase(client, type_ids, marker: str, user_headers, quantity: int = 2):
    return client.post("/api/v1/purchase-requests", json={
        "title": f"采购 GB300 {marker}",
        "items": [{
            "object_type_id": type_ids["SERVER"], "quantity": quantity,
            "model": "GB300", "unit_budget": "100000", "vendor": "NVIDIA",
        }],
        "currency": "CNY", "preferred_vendor": "NVIDIA",
        "justification": "Phase 3a integration test",
    }, headers=user_headers)


def test_purchase_receive_stock_deploy_full_lifecycle(client, type_ids, user_headers):
    marker = uuid4().hex
    purchase = _purchase(client, type_ids, marker, user_headers)
    assert purchase.status_code == 201, purchase.text
    purchase_id = purchase.json()["id"]
    assert purchase.json()["status"] == "PENDING"

    approved = client.post(f"/api/v1/purchase-requests/{purchase_id}/approve", json={"comment": "预算已确认"}, headers=user_headers)
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED"

    received = client.post("/api/v1/assets", json=[
        {"asset_number": f"AST-{marker}-1", "purchase_request_id": purchase_id,
         "object_type_id": type_ids["SERVER"], "name": f"GB300-{marker}-1",
         "serial_number": f"SN-{marker}-1", "model": "GB300", "spec_data": {"gpu_count": 8}},
        {"asset_number": f"AST-{marker}-2", "purchase_request_id": purchase_id,
         "object_type_id": type_ids["SERVER"], "name": f"GB300-{marker}-2",
         "serial_number": f"SN-{marker}-2", "model": "GB300"},
    ], headers=user_headers)
    assert received.status_code == 201, received.text
    assets = received.json()
    assert len(assets) == 2
    assert {item["lifecycle_status"] for item in assets} == {"RECEIVED"}

    rack = client.post("/api/v1/objects", json={"object_type_id": type_ids["RACK"], "name": f"Rack-{marker}"})
    assert rack.status_code == 201, rack.text
    premature = client.put(f"/api/v1/assets/{assets[0]['id']}/deploy", json={"location_id": rack.json()["id"]})
    assert premature.status_code == 409
    assert premature.json()["code"] == "InvalidAssetTransition"

    location = client.post("/api/v1/inventory-locations", json={
        "name": f"库存位-{marker}", "warehouse": "WH-A", "shelf": "S-01",
        "location_code": f"LOC-{marker}",
    }, headers=user_headers)
    assert location.status_code == 201, location.text
    for asset in assets:
        stocked = client.put(f"/api/v1/assets/{asset['id']}/stock", json={"inventory_location_id": location.json()["id"]}, headers=user_headers)
        assert stocked.status_code == 200, stocked.text
        assert stocked.json()["lifecycle_status"] == "STOCK"

    stock_listing = client.get("/api/v1/assets", params={"status": "STOCK"})
    assert stock_listing.status_code == 200
    assert {item["id"] for item in stock_listing.json()["items"]} >= {item["id"] for item in assets}

    deployed = client.put(f"/api/v1/assets/{assets[0]['id']}/deploy", json={"location_id": rack.json()["id"], "notes": "验收通过"}, headers=user_headers)
    assert deployed.status_code == 200, deployed.text
    assert deployed.json()["lifecycle_status"] == "ACTIVE"
    assert deployed.json()["object"]["deployed_location_id"] == rack.json()["id"]

    detail = client.get(f"/api/v1/assets/{assets[0]['id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["spec"]["gpu_count"] == 8
    assert detail.json()["deployment"]["acceptance_status"] == "ACCEPTED"

    timeline = client.get(f"/api/v1/assets/{assets[0]['id']}/lifecycle")
    assert timeline.status_code == 200, timeline.text
    statuses = [event["event_type"] for event in timeline.json()["items"]]
    assert statuses == ["REQUESTED", "APPROVED", "RECEIVED", "STOCK", "DEPLOYED", "ACTIVE"]

    active_at_rack = client.get("/api/v1/assets", params={"status": "ACTIVE", "location_id": rack.json()["id"]})
    assert active_at_rack.status_code == 200
    assert assets[0]["id"] in {item["id"] for item in active_at_rack.json()["items"]}


def test_unapproved_purchase_cannot_be_received(client, type_ids, user_headers):
    marker = uuid4().hex
    purchase = _purchase(client, type_ids, marker, user_headers, quantity=1)
    response = client.post("/api/v1/assets", json={
        "asset_number": f"AST-{marker}", "purchase_request_id": purchase.json()["id"],
        "object_type_id": type_ids["SERVER"], "name": f"unapproved-{marker}",
    }, headers=user_headers)
    assert response.status_code == 409
    assert response.json() == {"code": "PurchaseNotApproved", "message": "采购申请未批准，不能到货验收"}


def test_purchase_rejection(client, type_ids, user_headers):
    marker = uuid4().hex
    purchase = _purchase(client, type_ids, marker, user_headers, quantity=1)
    rejected = client.post(f"/api/v1/purchase-requests/{purchase.json()['id']}/reject", json={"rejection_reason": "预算不足"}, headers=user_headers)
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    repeated = client.post(f"/api/v1/purchase-requests/{purchase.json()['id']}/approve", json={})
    assert repeated.status_code == 409
