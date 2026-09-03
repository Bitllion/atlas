import csv
from io import BytesIO, StringIO
from uuid import uuid4

from openpyxl import Workbook


HEADERS = [
    "name", "object_type", "serial_number", "asset_number", "manufacturer",
    "model", "status", "ownership", "management_scope", "spec",
]


def _rows(marker: str, duplicate_serial: str) -> list[list[str]]:
    return [
        [f"import-valid-{marker}", "SERVER", f"new-sn-{marker}", "", "NVIDIA", "GB300", "ACTIVE", "OWNED", "FULL_CONTROL", '{"gpu_count": 8}'],
        [f"import-unknown-{marker}", "UNKNOWN_TYPE", f"unknown-sn-{marker}", "", "", "", "PLANNED", "OWNED", "NO_ACCESS", ""],
        [f"import-duplicate-{marker}", "SERVER", duplicate_serial, "", "", "", "PLANNED", "OWNED", "NO_ACCESS", ""],
    ]


def _xlsx(rows: list[list[str]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _csv(rows: list[list[str]]) -> bytes:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def _assert_atomic_invalid_import(client, extension: str, content: bytes, valid_name: str):
    preview = client.post(
        "/api/v1/import/preview",
        files={"file": (f"objects.{extension}", content)},
        data={"import_type": "object"},
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["status"] == "PREVIEWED"
    assert body["total_count"] == 3
    assert body["success_count"] == 1
    assert body["failed_count"] == 2
    assert {(item["row"], item["field"], item["error_type"]) for item in body["errors"]} == {
        (3, "object_type", "foreign_key"),
        (4, "serial_number", "duplicate"),
    }

    executed = client.post(f"/api/v1/import/{body['import_id']}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "FAILED"
    assert executed.json()["success_count"] == 0
    assert executed.json()["failed_count"] == 2
    assert client.get("/api/v1/objects", params={"name": valid_name}).json()["total"] == 0

    errors = client.get(f"/api/v1/import/{body['import_id']}/errors")
    assert errors.status_code == 200
    assert errors.json()["total"] == 2
    history = client.get("/api/v1/import/history", params={"page_size": 200})
    assert history.status_code == 200
    assert body["import_id"] in {item["id"] for item in history.json()["items"]}


def _existing_serial(client, type_ids, marker: str) -> str:
    serial = f"existing-sn-{marker}"
    response = client.post("/api/v1/objects", json={"object_type_id": type_ids["SERVER"], "name": f"existing-object-{marker}", "serial_number": serial})
    assert response.status_code == 201, response.text
    return serial


def test_xlsx_preview_errors_and_execute_rolls_back(client, type_ids):
    marker = uuid4().hex
    rows = _rows(marker, _existing_serial(client, type_ids, marker))
    _assert_atomic_invalid_import(client, "xlsx", _xlsx(rows), rows[0][0])


def test_utf8_bom_csv_preview_errors_and_execute_rolls_back(client, type_ids):
    marker = uuid4().hex
    rows = _rows(marker, _existing_serial(client, type_ids, marker))
    _assert_atomic_invalid_import(client, "csv", _csv(rows), rows[0][0])


def test_valid_xlsx_preview_and_execute(client):
    marker = uuid4().hex
    rows = [[f"import-success-{marker}", "GPU", f"success-sn-{marker}", "", "NVIDIA", "B300", "ACTIVE", "OWNED", "HARDWARE_ONLY", '{"memory_gb": 288}']]
    preview = client.post("/api/v1/import/preview", files={"file": ("valid.xlsx", _xlsx(rows))})
    assert preview.status_code == 200, preview.text
    executed = client.post(f"/api/v1/import/{preview.json()['import_id']}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "SUCCEEDED"
    assert executed.json()["success_count"] == 1
    detail = client.get("/api/v1/objects", params={"name": rows[0][0]}).json()
    assert detail["total"] == 1
