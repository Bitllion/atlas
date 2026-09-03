from uuid import uuid4


def test_object_crud_history_soft_delete_and_version_conflict(client, type_ids):
    marker = uuid4().hex
    created = client.post("/api/v1/objects", json={
        "object_type_id": type_ids["GPU"], "name": f"pytest-gpu-{marker}",
        "manufacturer": "NVIDIA", "model": "B300",
        "spec_data": {"memory": "288GB", "pci_bdf": "41:00.0"},
    })
    assert created.status_code == 201, created.text
    object_id = created.json()["id"]
    assert created.json()["version"] == 1

    listing = client.get("/api/v1/objects", params={"object_type": "GPU", "name": marker})
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    detail = client.get(f"/api/v1/objects/{object_id}")
    assert detail.status_code == 200
    assert detail.json()["spec_data"]["memory"] == "288GB"

    updated = client.put(f"/api/v1/objects/{object_id}", headers={"If-Match": "1"}, json={"status": "ACTIVE", "spec_data": {"memory": "288GB", "firmware": "97.00"}})
    assert updated.status_code == 200, updated.text
    assert updated.json()["version"] == 2

    conflict = client.put(f"/api/v1/objects/{object_id}", headers={"If-Match": "1"}, json={"name": "stale write"})
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "ConcurrentModificationError"

    history = client.get(f"/api/v1/objects/{object_id}/history")
    assert history.status_code == 200
    assert {item["change_type"] for item in history.json()["items"]} >= {"CREATE", "UPDATE"}
    update_event = next(item for item in history.json()["items"] if item["change_type"] == "UPDATE")
    assert update_event["before_data"]["status"] == "PLANNED"
    assert update_event["after_data"]["status"] == "ACTIVE"

    deleted = client.delete(f"/api/v1/objects/{object_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/objects/{object_id}").status_code == 404
    assert client.get("/api/v1/objects", params={"name": marker}).json()["total"] == 0


def test_create_object_idempotency_key(client, type_ids):
    marker = uuid4().hex
    payload = {"object_type_id": type_ids["RACK"], "name": f"pytest-idempotent-{marker}"}
    headers = {"Idempotency-Key": str(uuid4())}
    first = client.post("/api/v1/objects", json=payload, headers=headers)
    repeated = client.post("/api/v1/objects", json=payload, headers=headers)
    assert first.status_code == repeated.status_code == 201
    assert first.json()["id"] == repeated.json()["id"]
    conflict = client.post("/api/v1/objects", json={**payload, "name": f"changed-{marker}"}, headers=headers)
    assert conflict.status_code == 400
    assert conflict.json()["code"] == "IdempotencyKeyConflict"
