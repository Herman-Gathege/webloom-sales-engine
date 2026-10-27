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

    # ---- Sprint 3: authentication ------------------------------------
    # A development placeholder. `.env.example` explains how to replace it;
    # `validate_settings` refuses to run outside development with this value.
    jwt_secret_key: str = "dev-only-change-me-before-anything-real"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 8 * 60

    # Used only by `python -m app.bootstrap` to create the team's admin
    # accounts in local development. Never read at request time.
    bootstrap_admin_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_settings(settings: Settings) -> None:
    """Refuse obvious production misconfiguration instead of starting unsafely."""
    if settings.environment != "development":
        if settings.jwt_secret_key == "dev-only-change-me-before-anything-real":
            raise RuntimeError(
                "JWT_SECRET_KEY must be set to a real secret outside development."
            )
        if len(settings.jwt_secret_key) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters outside development.")
