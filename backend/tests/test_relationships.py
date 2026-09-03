from uuid import uuid4


def _object(client, object_type_id, name):
    response = client.post("/api/v1/objects", json={"object_type_id": object_type_id, "name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_create_filter_and_soft_delete_relationship(client, type_ids):
    marker = uuid4().hex
    server = _object(client, type_ids["SERVER"], f"pytest-server-{marker}")
    gpu = _object(client, type_ids["GPU"], f"pytest-gpu-rel-{marker}")
    created = client.post("/api/v1/relationships", json={
        "source_object_id": gpu,
        "relationship_type_id": type_ids["relation:installed_in"],
        "target_object_id": server,
    })
    assert created.status_code == 201, created.text
    relationship_id = created.json()["id"]
    listing = client.get("/api/v1/relationships", params={"source_id": gpu, "relation_type": "installed_in"})
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [relationship_id]
    assert client.delete(f"/api/v1/relationships/{relationship_id}").status_code == 204
    assert client.get("/api/v1/relationships", params={"source_id": gpu}).json()["items"] == []


def test_relationship_rejects_disallowed_types(client, type_ids):
    marker = uuid4().hex
    rack = _object(client, type_ids["RACK"], f"pytest-rack-{marker}")
    gpu = _object(client, type_ids["GPU"], f"pytest-invalid-gpu-{marker}")
    response = client.post("/api/v1/relationships", json={
        "source_object_id": rack,
        "relationship_type_id": type_ids["relation:installed_in"],
        "target_object_id": gpu,
    })
    assert response.status_code == 400
    assert response.json()["code"] == "InvalidRelationshipSource"
