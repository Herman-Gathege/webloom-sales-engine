"""Install the initial offer/template catalogue: `python -m app.catalog_seed`."""

from app.catalog_seed import seed_catalog
from app.database import SessionLocal


def main() -> int:
    with SessionLocal() as session:
        result = seed_catalog(session)
    print(
        "Catalogue seed: "
        f"{result.offers_created} offers created, {result.offers_present} present; "
        f"{result.templates_created} templates created, "
        f"{result.templates_present} present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
