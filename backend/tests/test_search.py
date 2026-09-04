"""Phase 5a cross-domain search tests."""

from uuid import uuid4

USER_ID = "7c17910d-850b-4a4b-bf93-e556984edab3"
HEADERS = {"X-User-Id": USER_ID}


def test_global_search_hits_each_resource_group(client, type_ids):
    marker = f"B300-{uuid4().hex}"
    obj = client.post("/api/v1/objects", json={"object_type_id": type_ids["GPU"], "name": f"GPU-{marker}", "serial_number": f"SN-{marker}", "model": marker})
    assert obj.status_code == 201, obj.text
    work_order = client.post("/api/v1/work-orders", headers=HEADERS, json={"title": f"排查 {marker}", "type": "FAULT", "priority": "MEDIUM", "object_id": obj.json()["id"]})
    assert work_order.status_code == 201, work_order.text
    article = client.post("/api/v1/knowledge/articles", headers=HEADERS, json={"title": f"{marker} 操作指南", "content": "操作内容", "type": "SOP"})
    assert article.status_code == 201, article.text

    response = client.get("/api/v1/search", params={"q": marker, "page_size": 100})
    assert response.status_code == 200, response.text
    payload = response.json()
    types = {item["resource_type"] for item in payload["items"]}
    assert {"object", "work_order", "knowledge_article"} <= types
    assert payload["total"] >= 3
    assert all({"resource_type", "id", "name", "summary"} <= item.keys() for item in payload["items"])


def test_search_validation_and_pagination(client):
    assert client.get("/api/v1/search", params={"q": ""}).json()["code"] == "ValidationError"
    response = client.get("/api/v1/search", params={"q": "B300", "page": 1, "page_size": 1})
    assert response.status_code == 200
    assert len(response.json()["items"]) <= 1
