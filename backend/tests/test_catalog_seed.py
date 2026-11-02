from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog_seed import seed_catalog
from app.models import MessageTemplate, Offer


def test_catalog_seed_installs_website_packages_and_templates(session: Session) -> None:
    result = seed_catalog(session)

    assert result.offers_created == 4
    offers = session.scalars(select(Offer).order_by(Offer.slug)).all()
    starter = next(offer for offer in offers if offer.slug == "starter-website")
    assert starter.price_min == Decimal("40000.00")
    assert starter.currency == "KES"
    assert len(session.scalars(select(MessageTemplate)).all()) >= 2


def test_catalog_seed_is_idempotent_and_preserves_edits(session: Session) -> None:
    seed_catalog(session)
    starter = session.scalar(select(Offer).where(Offer.slug == "starter-website"))
    assert starter is not None
    starter.name = "Starter Website — edited"
    session.commit()

    second = seed_catalog(session)
    session.refresh(starter)

    assert second.offers_created == 0
    assert second.offers_present == 4
    assert starter.name == "Starter Website — edited"
