"""Idempotent installation of Webloom's initial commercial catalogue."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MessageTemplate, Offer, TemplateChannel
from app.services.catalog_service import variables_in_body

OFFERS = (
    {
        "name": "Starter Website",
        "slug": "starter-website",
        "description": "A focused first website for a business establishing its online presence.",
        "price_min": Decimal("40000.00"),
        "price_max": Decimal("40000.00"),
        "currency": "KES",
        "pitch_angle": "A clear, useful website without an unnecessary rebuild.",
    },
    {
        "name": "Business Website",
        "slug": "business-website",
        "description": "A larger website for an established business with deeper content.",
        "price_min": None,
        "price_max": None,
        "currency": "KES",
        "pitch_angle": "More room to explain the business and turn interest into enquiries.",
    },
    {
        "name": "Custom Website",
        "slug": "custom-website",
        "description": "A scoped website for requirements beyond the standard packages.",
        "price_min": None,
        "price_max": None,
        "currency": "KES",
        "pitch_angle": "A defined solution after understanding the business requirement.",
    },
    {
        "name": "FikaTu Notification Platform",
        "slug": "fikatu-notification-platform",
        "description": "Reliable notification delivery for customer and operational messages.",
        "price_min": None,
        "price_max": None,
        "currency": "KES",
        "pitch_angle": "One delivery layer for the messages the business already needs to send.",
    },
)

TEMPLATES = (
    {
        "offer_slug": "starter-website",
        "channel": TemplateChannel.SMS,
        "name": "Website starter A",
        "variant": "A",
        "body": (
            "Hi {{business_name}}, I came across your business while researching "
            "{{area}}. We help businesses improve their online presence with "
            "{{offer_name}} ({{price_range}}). Would a short idea be useful? {{opt_out}}"
        ),
    },
    {
        "offer_slug": "starter-website",
        "channel": TemplateChannel.EMAIL,
        "name": "Website starter A",
        "variant": "A",
        "body": (
            "Hi {{business_name}} team,\n\n"
            "I came across your business while researching {{area}}. We help businesses "
            "improve their online presence with {{offer_name}} ({{price_range}}).\n\n"
            "Would it be useful if I shared one practical idea for your business?\n\n"
            "{{opt_out}}"
        ),
    },
)


@dataclass(frozen=True)
class CatalogSeedResult:
    offers_created: int
    offers_present: int
    templates_created: int
    templates_present: int


def seed_catalog(session: Session) -> CatalogSeedResult:
    offers_created = 0
    offers_present = 0
    offers_by_slug: dict[str, Offer] = {}

    for values in OFFERS:
        offer = session.scalar(select(Offer).where(Offer.slug == values["slug"]))
        if offer is None:
            offer = Offer(**values)
            session.add(offer)
            offers_created += 1
        else:
            offers_present += 1
        offers_by_slug[offer.slug] = offer

    session.flush()
    templates_created = 0
    templates_present = 0
    for values in TEMPLATES:
        offer = offers_by_slug[values["offer_slug"]]
        existing = session.scalar(
            select(MessageTemplate).where(
                MessageTemplate.offer_id == offer.id,
                MessageTemplate.channel == values["channel"],
                MessageTemplate.variant == values["variant"],
            )
        )
        if existing is not None:
            templates_present += 1
            continue
        body = str(values["body"])
        session.add(
            MessageTemplate(
                offer=offer,
                channel=values["channel"],
                name=str(values["name"]),
                variant=str(values["variant"]),
                body=body,
                variables=variables_in_body(body),
            )
        )
        templates_created += 1

    session.commit()
    return CatalogSeedResult(
        offers_created=offers_created,
        offers_present=offers_present,
        templates_created=templates_created,
        templates_present=templates_present,
    )
