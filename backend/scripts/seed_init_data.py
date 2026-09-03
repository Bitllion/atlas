"""Idempotently seed the Phase 1a object and relationship type catalogs."""

import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.dialects.postgresql import insert

# Allow direct execution as ``python scripts/seed_init_data.py`` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import settings


OBJECT_TYPES = [
    ("DATACENTER", "FACILITY", "数据中心"),
    ("ROOM", "FACILITY", "机房"),
    ("RACK", "FACILITY", "机柜"),
    ("SERVER", "IT", "服务器"),
    ("GPU", "IT", "GPU 加速卡"),
    ("NIC", "NETWORK", "网络接口卡"),
    ("CDU", "FACILITY", "冷却液分配单元"),
    ("POWER_SHELF", "POWER", "电源柜"),
]

RELATIONSHIP_TYPES = [
    {
        "name": "contains",
        "description": "包含",
        "is_directed": True,
        "allowed_source_types": ["DATACENTER", "ROOM", "RACK", "SERVER"],
        "allowed_target_types": ["ROOM", "RACK", "SERVER", "GPU", "NIC", "CDU", "POWER_SHELF"],
        "attributes_schema": {},
    },
    {
        "name": "installed_in",
        "description": "安装在",
        "is_directed": True,
        "allowed_source_types": ["SERVER", "GPU", "NIC"],
        "allowed_target_types": ["RACK", "SERVER"],
        "attributes_schema": {},
    },
    {
        "name": "connected_to",
        "description": "连接到",
        "is_directed": True,
        "allowed_source_types": ["NIC"],
        "allowed_target_types": ["NIC"],
        "attributes_schema": {"Speed": "string", "Protocol": "string"},
    },
    {
        "name": "feeds",
        "description": "供给",
        "is_directed": True,
        "allowed_source_types": ["CDU"],
        "allowed_target_types": ["RACK", "SERVER"],
        "attributes_schema": {"FlowRate": "number", "Temperature": "number"},
    },
    {
        "name": "powered_by",
        "description": "由其供电",
        "is_directed": True,
        "allowed_source_types": ["SERVER", "GPU"],
        "allowed_target_types": ["POWER_SHELF"],
        "attributes_schema": {},
    },
]


def upsert_rows(table: Table, rows: list[dict]) -> None:
    statement = insert(table).values(rows)
    mutable_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name not in {"id", "name", "created_at", "updated_at"}
        and any(column.name in row for row in rows)
    }
    mutable_columns["deleted_at"] = None
    mutable_columns["deleted_by"] = None
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.name],
        set_=mutable_columns,
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    metadata = MetaData()
    object_types = Table("object_types", metadata, autoload_with=engine)
    relationship_types = Table("relationship_types", metadata, autoload_with=engine)

    object_rows = [
        {
            "id": uuid4(),
            "name": name,
            "category": category,
            "description": description,
            "schema": {"type": "object", "properties": {}, "additionalProperties": True},
        }
        for name, category, description in OBJECT_TYPES
    ]
    relationship_rows = [dict(row, id=uuid4()) for row in RELATIONSHIP_TYPES]
    upsert_rows(object_types, object_rows)
    upsert_rows(relationship_types, relationship_rows)
    print(f"Seeded {len(object_rows)} object types and {len(RELATIONSHIP_TYPES)} relationship types.")
