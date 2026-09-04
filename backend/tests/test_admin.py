"""MVP administration, inventory-location, and attachment-download tests."""

from uuid import uuid4


def test_user_and_organization_crud_and_username_conflict(client):
    marker = uuid4().hex
    organization_response = client.post(
        "/api/v1/organizations",
        json={
            "name": f"admin-org-{marker}",
            "org_type": "INTERNAL",
            "contact": f"admin-{marker}@example.test",
        },
    )
    assert organization_response.status_code == 201, organization_response.text
    organization = organization_response.json()
    assert organization["contact"] == f"admin-{marker}@example.test"

    organizations = client.get(
        "/api/v1/organizations", params={"search": marker, "page": 1, "page_size": 10}
    )
    assert organizations.status_code == 200
    assert organizations.json()["total"] == 1
    assert organizations.json()["items"][0]["name"] == organization["name"]

    updated_organization = client.put(
        f"/api/v1/organizations/{organization['id']}",
        json={"name": f"renamed-org-{marker}", "is_active": False},
    )
    assert updated_organization.status_code == 200, updated_organization.text
    assert updated_organization.json()["is_active"] is False
    assert client.get(f"/api/v1/organizations/{organization['id']}").json()["name"] == f"renamed-org-{marker}"

    user_payload = {
        "username": f"admin-user-{marker}",
        "full_name": "Atlas Administrator",
        "email": f"admin-user-{marker}@example.test",
        "organization_id": organization["id"],
    }
    user_response = client.post("/api/v1/users", json=user_payload)
    assert user_response.status_code == 201, user_response.text
    user = user_response.json()
    assert user["organization_id"] == organization["id"]
    assert user["organization_name"] == f"renamed-org-{marker}"

    duplicate = client.post(
        "/api/v1/users",
        json={**user_payload, "email": f"other-{marker}@example.test"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json() == {"code": "UsernameConflict", "message": "用户名已存在"}

    users = client.get("/api/v1/users", params={"search": "Administrator"})
    assert users.status_code == 200
    assert user["id"] in {item["id"] for item in users.json()["items"]}

    updated_user = client.put(
        f"/api/v1/users/{user['id']}",
        json={"full_name": "Disabled Administrator", "is_active": False},
    )
    assert updated_user.status_code == 200, updated_user.text
    assert updated_user.json()["is_active"] is False
    assert client.get(f"/api/v1/users/{user['id']}").json()["full_name"] == "Disabled Administrator"


def test_inventory_locations_list(client):
    marker = uuid4().hex
    created = client.post(
        "/api/v1/inventory-locations",
        json={
            "location_code": f"LOC-{marker}",
            "name": f"Location {marker}",
            "warehouse": "WH-A",
            "shelf": "S-01",
            "description": "测试库存位置",
        },
    )
    assert created.status_code == 201, created.text
    response = client.get("/api/v1/inventory-locations", params={"page_size": 200})
    assert response.status_code == 200
    item = next(item for item in response.json()["items"] if item["location_code"] == f"LOC-{marker}")
    assert item["warehouse"] == "WH-A"
    assert item["shelf"] == "S-01"
    assert item["description"] == "测试库存位置"


def test_attachment_upload_download_roundtrip(client):
    marker = uuid4().hex
    organization = client.post(
        "/api/v1/organizations",
        json={"name": f"download-org-{marker}", "org_type": "INTERNAL"},
    ).json()
    user_response = client.post(
        "/api/v1/users",
        json={
            "username": f"download-user-{marker}",
            "email": f"download-{marker}@example.test",
            "organization_id": organization["id"],
        },
    )
    assert user_response.status_code == 201, user_response.text
    headers = {"X-User-Id": user_response.json()["id"]}
    article_response = client.post(
        "/api/v1/knowledge/articles",
        headers=headers,
        json={"title": f"download-{marker}", "content": "附件下载测试", "type": "SOP"},
    )
    assert article_response.status_code == 201, article_response.text
    article = article_response.json()
    content = b"atlas attachment roundtrip\n"
    upload_response = client.post(
        f"/api/v1/knowledge/articles/{article['id']}/attachments",
        headers=headers,
        files={"file": ("roundtrip.txt", content, "text/plain")},
    )
    assert upload_response.status_code == 201, upload_response.text
    attachment = upload_response.json()

    download = client.get(
        f"/api/v1/knowledge/articles/{article['id']}/attachments/{attachment['id']}/download"
    )
    assert download.status_code == 200, download.text
    assert download.content == content
    assert "roundtrip.txt" in download.headers["content-disposition"]

    missing = client.get(
        f"/api/v1/knowledge/articles/{article['id']}/attachments/{uuid4()}/download"
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "AttachmentNotFound"
