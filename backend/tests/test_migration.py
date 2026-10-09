"""The migration, on a clean database of its own — and back again."""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from tests.conftest import require_test_database_url, run_migrations

TABLES = {"leads", "activities"}


@pytest.fixture
def migration_database_url() -> Iterator[str]:
    """A dedicated, empty database for the migration round trip."""
    base_url = make_url(require_test_database_url())
    database_name = f"{base_url.database}_migration_test"
    admin_url = base_url.set(database="postgres")
    # render_as_string(hide_password=False), not str(): SQLAlchemy's URL.__str__ masks the
    # password as "***", which only works where PostgreSQL does not ask for one.
    migration_url = base_url.set(database=database_name).render_as_string(hide_password=False)

    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    admin.dispose()

    try:
        yield migration_url
    finally:
        admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin.connect() as connection:
            connection.execute(
                text(
                    "select pg_terminate_backend(pid) from pg_stat_activity "
                    "where datname = :name"
                ),
                {"name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin.dispose()


def _table_names(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migration_up_and_down_on_a_clean_database(migration_database_url: str) -> None:
    # Upgrade from empty.
    run_migrations(migration_database_url, "upgrade", "head")
    assert TABLES <= _table_names(migration_database_url)

    engine = create_engine(migration_database_url)
    try:
        inspector = inspect(engine)

        lead_columns = {column["name"] for column in inspector.get_columns("leads")}
        assert lead_columns == {
            "id",
            "business_name",
            "sector",
            "area",
            "phone",
            "whatsapp_capable",
            "website_status",
            "has_website",
            "source",
            "status",
            "created_at",
            "updated_at",
        }

        activity_columns = {column["name"] for column in inspector.get_columns("activities")}
        assert activity_columns == {
            "id",
            "lead_id",
            "type",
            "actor",
            "summary",
            "created_at",
        }

        # Integrity rules the contract asks for, named as the models name them.
        assert {constraint["name"] for constraint in inspector.get_unique_constraints("leads")} == {
            "uq_leads_phone"
        }
        assert {constraint["name"] for constraint in inspector.get_check_constraints("leads")} >= {
            "ck_leads_business_name_not_blank",
            "ck_leads_source_not_blank",
        }

        indexes = {index["name"] for index in inspector.get_indexes("activities")}
        assert "ix_activities_lead_id_created_at" in indexes

        foreign_keys = inspector.get_foreign_keys("activities")
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "leads"
        assert foreign_keys[0]["options"].get("ondelete") == "CASCADE"
    finally:
        engine.dispose()

    # Reversible: down drops both tables, up builds them again.
    run_migrations(migration_database_url, "downgrade", "base")
    assert TABLES.isdisjoint(_table_names(migration_database_url))

    run_migrations(migration_database_url, "upgrade", "head")
    assert TABLES <= _table_names(migration_database_url)


def test_the_test_database_name_is_guarded() -> None:
    previous = os.environ.get("TEST_DATABASE_URL")
    os.environ["TEST_DATABASE_URL"] = "postgresql+psycopg://postgres@localhost/not_a_test_db"
    try:
        with pytest.raises(RuntimeError, match="must end in '_test'"):
            require_test_database_url()
    finally:
        if previous is None:
            os.environ.pop("TEST_DATABASE_URL", None)
        else:
            os.environ["TEST_DATABASE_URL"] = previous
