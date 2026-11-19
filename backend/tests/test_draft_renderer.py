"""Deterministic rendering and standard SMS segmentation."""

from decimal import Decimal

from app.models import Lead, MessageTemplate, Offer, TemplateChannel
from app.services.draft_renderer import OPT_OUT_TEXT, render_draft, sms_metrics


def sample_offer(**overrides: object) -> Offer:
    values: dict[str, object] = {
        "name": "Starter Website",
        "slug": "starter-website",
        "price_min": Decimal("40000.00"),
        "price_max": None,
        "currency": "KES",
        "pitch_angle": "A clear website.",
        "is_active": True,
    }
    values.update(overrides)
    return Offer(**values)


def sample_template(body: str) -> MessageTemplate:
    return MessageTemplate(
        offer_id=None,
        channel=TemplateChannel.SMS,
        name="Synthetic",
        variant="A",
        body=body,
        variables=[],
        is_active=True,
    )


def sample_lead(**overrides: object) -> Lead:
    values: dict[str, object] = {
        "business_name": "Synthetic Pharmacy",
        "sector": "Pharmacies",
        "area": "Westlands",
        "phone": "+254700990301",
        "website_status": "no website listed",
        "has_website": False,
        "website_presence": "no_website",
        "source": "yellow_pages_kenya_listing",
    }
    values.update(overrides)
    return Lead(**values)


def test_renderer_resolves_approved_values_and_canonical_opt_out() -> None:
    rendered, failure = render_draft(
        sample_template(
            "Hi {{business_name}} in {{area}}. {{offer_name}} is {{price_range}}. "
            "{{opt_out}}"
        ),
        sample_lead(),
        sample_offer(),
    )

    assert failure is None
    assert rendered == (
        "Hi Synthetic Pharmacy in Westlands. Starter Website is "
        f"From KES 40,000. {OPT_OUT_TEXT}"
    )


def test_unknown_website_skips_website_dependent_copy() -> None:
    rendered, failure = render_draft(
        sample_template("{{business_name}} has {{has_website}}. {{opt_out}}"),
        sample_lead(
            website_status="website not checked",
            website_presence="unknown",
        ),
        sample_offer(),
    )

    assert rendered is None
    assert failure is not None
    assert failure.code == "missing_template_data:has_website"


def test_unknown_website_skips_raw_website_status_copy() -> None:
    rendered, failure = render_draft(
        sample_template("{{business_name}} reports: {{website_status}}. {{opt_out}}"),
        sample_lead(
            website_status="some unverified result",
            website_presence="unknown",
        ),
        sample_offer(),
    )

    assert rendered is None
    assert failure is not None
    assert failure.code == "unknown_website_research:website_status"


def test_missing_price_skips_price_dependent_copy() -> None:
    rendered, failure = render_draft(
        sample_template("{{business_name}} costs {{price_range}}. {{opt_out}}"),
        sample_lead(),
        sample_offer(price_min=None, price_max=None),
    )

    assert rendered is None
    assert failure is not None
    assert failure.code == "missing_template_data:price_range"


def test_price_range_uses_sms_safe_separator() -> None:
    rendered, failure = render_draft(
        sample_template("{{business_name}}: {{price_range}}. {{opt_out}}"),
        sample_lead(),
        sample_offer(price_min=Decimal("40000.00"), price_max=Decimal("60000.00")),
    )

    assert failure is None
    assert "KES 40,000 - KES 60,000" in (rendered or "")
    assert sms_metrics(rendered or "").encoding == "gsm-7"


def test_renderer_is_channel_generic_for_email_templates() -> None:
    template = sample_template("Hello {{business_name}}.\n\n{{opt_out}}")
    template.channel = TemplateChannel.EMAIL

    rendered, failure = render_draft(template, sample_lead(), sample_offer())

    assert failure is None
    assert rendered == f"Hello Synthetic Pharmacy.\n\n{OPT_OUT_TEXT}"


def test_sms_segmentation_handles_gsm_extensions_and_unicode() -> None:
    gsm = sms_metrics("a" * 160)
    extended = sms_metrics("€" * 81)
    unicode_message = sms_metrics("Habari 👋")

    assert (gsm.encoding, gsm.units, gsm.segments) == ("gsm-7", 160, 1)
    assert (extended.encoding, extended.units, extended.segments) == (
        "gsm-7",
        162,
        2,
    )
    assert unicode_message.encoding == "ucs-2"
    assert unicode_message.units == 9
    assert unicode_message.segments == 1

    unicode_concatenated = sms_metrics("👋" * 36)
    assert unicode_concatenated.units == 72
    assert unicode_concatenated.segments == 2
