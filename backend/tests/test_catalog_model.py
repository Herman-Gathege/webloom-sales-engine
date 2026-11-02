from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import MessageTemplate, Offer, TemplateChannel


def test_offer_accepts_multi_currency_price_guidance(session: Session) -> None:
    offer = Offer(
        name="Starter Website",
        slug="starter-website",
        description="A focused first website.",
        price_min=Decimal("40000.00"),
        price_max=Decimal("40000.00"),
        currency="KES",
        pitch_angle="Get online without losing the personal service.",
    )
    session.add(offer)
    session.commit()

    saved = session.get(Offer, offer.id)
    assert saved is not None
    assert saved.currency == "KES"
    assert saved.price_min == Decimal("40000.00")
    assert saved.is_active is True


def test_offer_rejects_duplicate_slug(session: Session) -> None:
    session.add(Offer(name="First", slug="same-slug"))
    session.commit()
    session.add(Offer(name="Second", slug="same-slug"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_offer_rejects_invalid_currency_and_price_range(session: Session) -> None:
    session.add(
        Offer(
            name="Invalid",
            slug="invalid-offer",
            currency="kes",
            price_min=Decimal("2"),
            price_max=Decimal("1"),
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_template_belongs_to_offer_and_channel(session: Session) -> None:
    offer = Offer(name="Starter Website", slug="starter-website")
    template = MessageTemplate(
        offer=offer,
        channel=TemplateChannel.SMS,
        name="No website A",
        variant="A",
        body="Hi {{business_name}}. {{opt_out}}",
        variables=["business_name", "opt_out"],
    )
    session.add(template)
    session.commit()

    assert template.offer is offer
    assert template.channel is TemplateChannel.SMS
    assert template.is_active is True


def test_template_variant_is_unique_per_offer_and_channel(session: Session) -> None:
    offer = Offer(name="Starter Website", slug="starter-website")
    session.add_all(
        [
            MessageTemplate(
                offer=offer,
                channel=TemplateChannel.EMAIL,
                name="First",
                variant="A",
                body="First {{opt_out}}",
                variables=["opt_out"],
            ),
            MessageTemplate(
                offer=offer,
                channel=TemplateChannel.EMAIL,
                name="Duplicate",
                variant="A",
                body="Second {{opt_out}}",
                variables=["opt_out"],
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_template_rejects_blank_body(session: Session) -> None:
    offer = Offer(name="Starter Website", slug="starter-website")
    session.add(
        MessageTemplate(
            offer=offer,
            channel=TemplateChannel.SMS,
            name="Blank",
            variant="A",
            body="",
            variables=[],
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()
