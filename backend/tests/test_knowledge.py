"""Phase 5a knowledge lifecycle, attachment, and object-link tests."""

from uuid import uuid4

USER_ID = "7c17910d-850b-4a4b-bf93-e556984edab3"
HEADERS = {"X-User-Id": USER_ID}


def test_knowledge_article_lifecycle_attachment_and_links(client, type_ids):
    marker = uuid4().hex
    obj = client.post("/api/v1/objects", json={"object_type_id": type_ids["GPU"], "name": f"knowledge-gpu-{marker}", "model": "B300"})
    assert obj.status_code == 201, obj.text

    created = client.post("/api/v1/knowledge/articles", headers=HEADERS, json={"title": f"GPU 更换流程 {marker}", "content": "检查、断电并更换 GPU。", "type": "SOP", "tags": ["GPU", "B300"]})
    assert created.status_code == 201, created.text
    article = created.json()
    assert article["status"] == "DRAFT"
    assert article["version"] == 1

    updated = client.put(f"/api/v1/knowledge/articles/{article['id']}", headers=HEADERS, json={"content": "检查、断电、更换并验证 GPU。"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["version"] == 2

    linked = client.post(f"/api/v1/knowledge/articles/{article['id']}/link-objects", headers=HEADERS, json={"objects": [obj.json()["id"]], "relation_reason": "适用于 B300"})
    assert linked.status_code == 200, linked.text
    assert linked.json()["items"][0]["object_name"] == f"knowledge-gpu-{marker}"

    attached = client.post(f"/api/v1/knowledge/articles/{article['id']}/attachments", headers=HEADERS, files={"file": ("gpu-sop.txt", b"safe procedure", "text/plain")})
    assert attached.status_code == 201, attached.text
    assert attached.json()["file_name"] == "gpu-sop.txt"
    assert attached.json()["file_size"] == 14

    published = client.post(f"/api/v1/knowledge/articles/{article['id']}/publish", headers=HEADERS)
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "PUBLISHED"
    assert published.json()["published_at"] is not None
    assert client.put(f"/api/v1/knowledge/articles/{article['id']}", headers=HEADERS, json={"title": "不可直接编辑"}).json()["code"] == "ArticleNotEditable"

    listing = client.get("/api/v1/knowledge/articles", params={"type": "SOP", "status": "PUBLISHED"}).json()
    assert article["id"] in {item["id"] for item in listing["items"]}
    detail = client.get(f"/api/v1/knowledge/articles/{article['id']}").json()
    assert len(detail["attachments"]) == len(detail["links"]) == 1

    unlinked = client.request("DELETE", f"/api/v1/knowledge/articles/{article['id']}/link-objects", headers=HEADERS, json={"objects": [obj.json()["id"]]})
    assert unlinked.status_code == 200
    assert unlinked.json()["items"] == []
