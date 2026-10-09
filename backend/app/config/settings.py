"""Application settings, read from the environment (and backend/.env if present)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Webloom Sales Engine API"

    # One place knows the connection string. Alembic and the app both read it
    # from here, from the DATABASE_URL environment variable.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/webloom_sales_engine"

    # "development" or "test" locally. The seed command refuses to run against
    # "production" so a demo fixture can never be poured into a real database.
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"

    sql_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
