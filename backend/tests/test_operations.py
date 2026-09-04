from uuid import uuid4


USER_ID = "7c17910d-850b-4a4b-bf93-e556984edab3"
HEADERS = {"X-User-Id": USER_ID}


def _object(client, type_id, name):
    response = client.post("/api/v1/objects", json={"object_type_id": type_id, "name": name, "status": "ACTIVE"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_work_order_full_lifecycle_and_object_query(client, type_ids):
    marker = uuid4().hex
    old_object_id = _object(client, type_ids["GPU"], f"operations-old-{marker}")
    new_object_id = _object(client, type_ids["GPU"], f"operations-new-{marker}")

    created = client.post("/api/v1/work-orders", headers=HEADERS, json={
        "title": "GPU 温度过高", "type": "FAULT", "priority": "HIGH",
        "object_id": old_object_id, "description": "持续触发温度告警",
    })
    assert created.status_code == 201, created.text
    work_order = created.json()
    assert work_order["status"] == "CREATED"
    assert work_order["work_order_number"].startswith("WO-")

    illegal = client.put(f"/api/v1/work-orders/{work_order['id']}/close", headers=HEADERS)
    assert illegal.status_code == 409
    assert illegal.json()["code"] == "InvalidWorkOrderTransition"

    assigned = client.put(f"/api/v1/work-orders/{work_order['id']}/assign", headers=HEADERS,
                          json={"assignee_id": USER_ID})
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "ASSIGNED"

    repaired = client.post(f"/api/v1/work-orders/{work_order['id']}/repairs", headers=HEADERS, json={
        "repair_type": "REPLACEMENT", "description": "检查散热器并更换风扇模块",
        "repair_result": "SUCCESS", "parts_used": [{"name": "风扇模块", "quantity": 1}],
    })
    assert repaired.status_code == 201, repaired.text
    repair_id = repaired.json()["id"]
    assert client.get(f"/api/v1/work-orders/{work_order['id']}").json()["status"] == "PROCESSING"

    replaced = client.post(f"/api/v1/work-orders/{work_order['id']}/replacements", headers=HEADERS, json={
        "repair_record_id": repair_id, "old_object_id": old_object_id, "new_object_id": new_object_id,
        "replacement_reason": "FAILURE", "old_object_disposition": "RMA", "notes": "风扇失效",
    })
    assert replaced.status_code == 201, replaced.text
    assert client.get(f"/api/v1/objects/{old_object_id}").json()["status"] == "MAINTENANCE"

    resolved = client.put(f"/api/v1/work-orders/{work_order['id']}/resolve", headers=HEADERS)
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "RESOLVED"
    closed = client.put(f"/api/v1/work-orders/{work_order['id']}/close", headers=HEADERS)
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "CLOSED"

    detail = client.get(f"/api/v1/work-orders/{work_order['id']}")
    assert detail.status_code == 200
    assert len(detail.json()["repairs"]) == len(detail.json()["replacements"]) == 1
    assert {event["status"] for event in detail.json()["timeline"] if event["type"] == "STATUS"} >= {"CREATED", "ASSIGNED", "PROCESSING", "RESOLVED", "CLOSED"}

    timeline = client.get(f"/api/v1/work-orders/{work_order['id']}/timeline")
    assert timeline.status_code == 200
    assert {event["type"] for event in timeline.json()["items"]} >= {"STATUS", "REPAIR", "REPLACEMENT"}

    listing = client.get("/api/v1/work-orders", params={"status": "CLOSED", "type": "FAULT", "object_id": old_object_id})
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    object_orders = client.get(f"/api/v1/objects/{old_object_id}/work-orders")
    assert object_orders.status_code == 200
    assert [item["id"] for item in object_orders.json()["items"]] == [work_order["id"]]


def test_explicit_start_and_invalid_transition(client, type_ids):
    object_id = _object(client, type_ids["SERVER"], f"operations-start-{uuid4().hex}")
    created = client.post("/api/v1/work-orders", headers=HEADERS, json={
        "title": "服务器巡检", "type": "INSPECTION", "priority": "LOW", "related_object_id": object_id,
    })
    work_order_id = created.json()["id"]
    assert client.put(f"/api/v1/work-orders/{work_order_id}/start", headers=HEADERS).status_code == 409
    assert client.put(f"/api/v1/work-orders/{work_order_id}/assign", headers=HEADERS, json={"assigned_to": USER_ID}).status_code == 200
    started = client.put(f"/api/v1/work-orders/{work_order_id}/start", headers=HEADERS)
    assert started.status_code == 200
    assert started.json()["status"] == "PROCESSING"
