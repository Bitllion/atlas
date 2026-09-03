# Atlas backend

## Object import template

`POST /api/v1/import/preview` accepts UTF-8/UTF-8-BOM CSV files and `.xlsx` workbooks. The first worksheet is used. Supported columns are:

| Column | Required | Description |
| --- | --- | --- |
| `name` | yes | Unique object name |
| `object_type` | yes | Active object type name such as `RACK`, `SERVER`, `GPU`, `NIC`, or its UUID |
| `serial_number` | no | Manufacturer serial number; duplicates are rejected |
| `asset_number` | no | Internal asset number |
| `manufacturer` | no | Manufacturer |
| `model` | no | Model |
| `status` | no | `PLANNED`, `ACTIVE`, `INACTIVE`, `MAINTENANCE`, or `RETIRED`; defaults to `PLANNED` |
| `ownership` | no | `OWNED`, `CUSTOMER_OWNED`, or `THIRD_PARTY`; defaults to `OWNED` |
| `management_scope` | no | `FULL_CONTROL`, `HARDWARE_ONLY`, `MAINTENANCE_ONLY`, or `NO_ACCESS`; defaults to `NO_ACCESS` |
| `spec` | no | JSON object encoded as a string; stored as an IMPORT-sourced object specification |

Preview persists normalized data in `import_jobs.preview_data`; execution uses the returned `import_id` and does not require another upload. Execution is atomic: validation or persistence errors leave no imported objects behind.
