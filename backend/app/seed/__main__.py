"""Seed the sample leads: `python -m app.seed` from the backend directory.

Refuses to run against a production database. The demo fixture is for local
development and tests only (AGENTS.md: sample data never touches production).
"""

import sys

from app.config import get_settings
from app.database import SessionLocal
from app.seed import seed_sample_leads


def main() -> int:
    settings = get_settings()

    if settings.environment.lower() in {"production", "prod"}:
        print(
            "Refusing to seed: ENVIRONMENT is production. "
            "The sample leads are synthetic demo data.",
            file=sys.stderr,
        )
        return 1

    with SessionLocal() as session:
        result = seed_sample_leads(session)

    print(f"Seeded sample leads into {settings.database_url.split('@')[-1]}")
    print(f"  {result.describe()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
