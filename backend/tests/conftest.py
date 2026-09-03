"""Shared API test fixtures backed by the local Phase 1 PostgreSQL database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models import ObjectType, RelationshipType


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def type_ids() -> dict[str, str]:
    with SessionLocal() as db:
        object_types = {item.name: str(item.id) for item in db.scalars(select(ObjectType).where(ObjectType.deleted_at.is_(None)))}
        relationship_types = {item.name: str(item.id) for item in db.scalars(select(RelationshipType).where(RelationshipType.deleted_at.is_(None)))}
    return {**object_types, **{f"relation:{key}": value for key, value in relationship_types.items()}}
