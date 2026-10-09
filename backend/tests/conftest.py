"""Test fixtures.

These tests run against a real PostgreSQL database — the same engine the
product uses (ADR-001). Nothing here mocks the session or the database, and
nothing writes outside the test database: the suite refuses to run unless the
database name ends in "_test".

Each test runs inside its own transaction that is rolled back afterwards, so
tests cannot see each other's rows even though they share one database.
"""

import itertools
import os
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from alembic import command
from alembic.config import Config
from app.config import get_settings
from app.database import get_session
from app.main import app
from app.models import Lead, LeadStatus

BACKEND_DIR = Path(__file__).resolve().parents[1]

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5432/webloom_sales_engine_test"
)


def require_test_database_url() -> str:
    """TEST_DATABASE_URL, or a local default. Never anything but a *_test database."""
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    database_name = make_url(url).database or ""
    if not database_name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run the suite against database {database_name!r}: "
            "its name must end in '_test'. Set TEST_DATABASE_URL."
        )
    return url


def run_migrations(database_url: str, *args: str) -> None:
    """Drive Alembic the way a person would, with the URL in DATABASE_URL."""
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        config = Config(str(BACKEND_DIR / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        getattr(command, args[0])(config, *args[1:])
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """A migrated test database, built from scratch by the migration itself."""
    database_url = require_test_database_url()

    admin = create_engine(database_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    admin.dispose()

    run_migrations(database_url, "upgrade", "head")

    test_engine = create_engine(database_url)
    try:
        yield test_engine
    finally:
        test_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """A session whose work is thrown away at the end of the test."""
    connection = engine.connect()
    transaction = connection.begin()
    test_session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield test_session
    finally:
        test_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """The real app, using the test's session."""
    app.dependency_overrides[get_session] = lambda: session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_lead() -> Iterator[Callable[..., Lead]]:
    """Orders with sane defaults; override any field by keyword."""
    counter = itertools.count(1)

    def factory(**overrides: object) -> Lead:
        number = next(counter)
        values: dict[str, object] = {
            "id": uuid.uuid4(),
            "business_name": f"Test Business {number}",
            "sector": "Opticians and eyewear",
            "area": "CBD",
            # Synthetic, in the +2547000... range the sample data reserves.
            "phone": f"+2547000{number:05d}",
            "whatsapp_capable": True,
            "website_status": f"{number} reviews - no website listed",
            "has_website": False,
            "source": "google_maps",
            "status": LeadStatus.NEW,
        }
        values.update(overrides)
        return Lead(**values)

    yield factory
