"""Deterministic template rendering and SMS segment accounting."""

import math
import re
from dataclasses import dataclass
from decimal import Decimal

from app.models import Lead, MessageTemplate, Offer

OPT_OUT_TEXT = "Reply STOP to opt out."
VARIABLE_TOKEN = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")

GSM7_BASIC = (
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./"
    "0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿"
    "abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM7_EXTENSION = "^{}\\[~]|€"


@dataclass(frozen=True)
class RenderFailure:
    code: str
    message: str


@dataclass(frozen=True)
class SmsMetrics:
    encoding: str
    characters: int
    units: int
    segments: int


def format_price_range(offer: Offer) -> str | None:
    if offer.price_min is None and offer.price_max is None:
        return None
    if offer.price_min is not None:
        minimum = _format_money(offer.price_min, offer.currency)
    else:
        minimum = None
    if offer.price_max is not None:
        maximum = _format_money(offer.price_max, offer.currency)
    else:
        maximum = None

    if minimum is not None and maximum is not None:
        if offer.price_min == offer.price_max:
            return minimum
        return f"{minimum} - {maximum}"
    if minimum is not None:
        return f"From {minimum}"
    return f"Up to {maximum}"


def render_draft(
    template: MessageTemplate,
    lead: Lead,
    offer: Offer,
) -> tuple[str | None, RenderFailure | None]:
    """Render using resolved values only; never leave an unresolved placeholder."""
    variables = {
        "business_name": lead.business_name.strip(),
        "sector": lead.sector,
        "area": lead.area,
        "website_status": lead.website_status,
        "has_website": _website_phrase(lead),
        "offer_name": offer.name,
        "price_range": format_price_range(offer),
        "pitch_angle": offer.pitch_angle,
        "opt_out": OPT_OUT_TEXT,
    }
    required = sorted(set(VARIABLE_TOKEN.findall(template.body)))
    missing = [name for name in required if not variables.get(name)]
    if missing:
        names = ", ".join(missing)
        return None, RenderFailure(
            code=f"missing_template_data:{missing[0]}",
            message=f"Template data is missing: {names}.",
        )
    if lead.website_presence == "unknown":
        website_variable = next(
            (
                name
                for name in required
                if name in {"website_status", "has_website"}
            ),
            None,
        )
        if website_variable is not None:
            return None, RenderFailure(
                code=f"unknown_website_research:{website_variable}",
                message="Website research is not verified for this lead.",
            )

    rendered = VARIABLE_TOKEN.sub(
        lambda match: str(variables[match.group(1)]),
        template.body,
    ).strip()
    if "{{" in rendered or "}}" in rendered:
        return None, RenderFailure(
            code="malformed_template_variable",
            message="The template contains a placeholder that cannot be rendered.",
        )
    if not rendered:
        return None, RenderFailure(
            code="empty_rendered_draft",
            message="The rendered draft is empty.",
        )
    return rendered, None


def sms_metrics(body: str) -> SmsMetrics:
    """Count GSM-7 septets or UCS-2 code units and apply standard segmentation."""
    if all(character in GSM7_BASIC or character in GSM7_EXTENSION for character in body):
        units = sum(
            2 if character in GSM7_EXTENSION else 1
            for character in body
        )
        segments = 1 if units <= 160 else math.ceil(units / 153)
        return SmsMetrics(
            encoding="gsm-7",
            characters=len(body),
            units=units,
            segments=segments,
        )

    units = len(body.encode("utf-16-le")) // 2
    segments = 1 if units <= 70 else math.ceil(units / 67)
    return SmsMetrics(
        encoding="ucs-2",
        characters=len(body),
        units=units,
        segments=segments,
    )


def _website_phrase(lead: Lead) -> str | None:
    if lead.website_presence == "has_website":
        return "has a website"
    if lead.website_presence == "no_website":
        return "no website found"
    return None


def _format_money(value: Decimal, currency: str) -> str:
    amount = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{currency} {amount}"
