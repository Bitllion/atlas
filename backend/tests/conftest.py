"""Shared API test fixtures backed by a disposable PostgreSQL database."""

import os
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import close_all_sessions


DEFAULT_DATABASE_URL = "postgresql+psycopg://atlas:atlas@localhost:55433/atlas"


def _test_database_url() -> URL:
    explicit_test_url = os.getenv("TEST_DATABASE_URL")
    configured = explicit_test_url or os.getenv("DATABASE_URL") or os.getenv("ATLAS_DATABASE_URL")
    url = make_url(configured or DEFAULT_DATABASE_URL)
    if explicit_test_url is None:
        url = url.set(database="atlas_test")
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Atlas integration tests require PostgreSQL")
    if url.database in {None, "atlas", "postgres", "template0", "template1"}:
        raise RuntimeError(f"Refusing to run tests against protected database {url.database!r}")
    return url


# This must happen before importing app.database.session, whose engine is global.
TEST_DATABASE_URL = _test_database_url()
os.environ["DATABASE_URL"] = TEST_DATABASE_URL.render_as_string(hide_password=False)

from app.database.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ObjectType, Organization, RelationshipType, User  # noqa: E402
from scripts.seed_init_data import seed_initial_data  # noqa: E402


def _drop_database(connection, database_name: str) -> None:
    connection.execute(
        text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :database AND pid <> pg_backend_pid()"
        ),
        {"database": database_name},
    )
    quoted_name = connection.dialect.identifier_preparer.quote(database_name)
    connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quoted_name}")


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Iterator[None]:
    """Recreate, migrate, seed, and finally remove the isolated test database."""
    maintenance_url = TEST_DATABASE_URL.set(database="postgres")
    maintenance_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    database_name = TEST_DATABASE_URL.database
    assert database_name is not None
    with maintenance_engine.connect() as connection:
        _drop_database(connection, database_name)
        quoted_name = connection.dialect.identifier_preparer.quote(database_name)
        connection.exec_driver_sql(f"CREATE DATABASE {quoted_name}")

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_config = Config(str(backend_dir / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_config.set_main_option(
        "sqlalchemy.url", TEST_DATABASE_URL.render_as_string(hide_password=False)
    )
    command.upgrade(alembic_config, "head")
    seed_initial_data(engine)
    with SessionLocal.begin() as session:
        organization = Organization(name="Atlas Test Organization", org_type="INTERNAL")
        session.add(organization)
        session.flush()
        session.add(
            User(
                id=UUID("7c17910d-850b-4a4b-bf93-e556984edab3"),
                username="atlas-test-user",
                email="atlas-test@example.test",
                password_hash="test-only",
                organization_id=organization.id,
            )
        )

    try:
        yield
    finally:
        close_all_sessions()
        engine.dispose()
        with maintenance_engine.connect() as connection:
            _drop_database(connection, database_name)
        maintenance_engine.dispose()


@pytest.fixture(scope="session")
def client(test_database) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def type_ids(test_database) -> dict[str, str]:
    with SessionLocal() as db:
        object_types = {item.name: str(item.id) for item in db.scalars(select(ObjectType).where(ObjectType.deleted_at.is_(None)))}
        relationship_types = {item.name: str(item.id) for item in db.scalars(select(RelationshipType).where(RelationshipType.deleted_at.is_(None)))}
    return {**object_types, **{f"relation:{key}": value for key, value in relationship_types.items()}}
