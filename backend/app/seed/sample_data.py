"""Synthetic sample leads for the Epic 1 demo.

Every value here is invented, including the phone numbers and business names.
Real lead data lives in the gitignored `data/` directory and is never committed
here (AGENTS.md non-negotiable 4).

The first six businesses match `frontend/src/api/fixtures.ts`, so the Lead List
and Lead Detail screens show the same leads before and after the API answers.
The last two exercise the fields the first six leave alone: a lead that already
has a website, a lead with no phone yet, and a lead with no sector.

Ids and timestamps are fixed, not random: seeding twice must not create a second
copy of anything.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.models import Activity, Lead, LeadStatus

SOURCE = "google_maps"

# The first six leads are added one minute apart, so "newest first" has a
# visible, deterministic order.
SEED_START = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)


def _seed_id(n: int) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-4000-8000-{n:012d}")


def _activity_id(n: int) -> uuid.UUID:
    return uuid.UUID(f"10000000-0000-4000-8000-{n:012d}")


# (business_name, sector, area, phone, whatsapp_capable, website_status, has_website)
SAMPLE_LEADS: tuple[tuple[Any, ...], ...] = (
    (
        "Mwangaza Opticians",
        "Opticians and eyewear",
        "CBD, 3 branches",
        "+254700000101",
        True,
        "3,713 reviews - no website listed",
        False,
    ),
    (
        "Green Valley Agrovet",
        "Agrovets and agri-input suppliers",
        "Kiambu Road",
        "+254700000102",
        True,
        "212 reviews - no website listed",
        False,
    ),
    (
        "Riverside Dental Centre",
        "Clinics, dental and medical centres",
        "Westlands",
        "+254700000103",
        True,
        "488 reviews - Facebook page only",
        False,
    ),
    (
        "Sokoni Hardware and Electricals",
        "Hardware, electrical and security suppliers",
        "Industrial Area",
        "+254700000104",
        True,
        "76 reviews - no website listed",
        False,
    ),
    (
        "Swiftline Logistics",
        "Logistics, freight and removals",
        "Mombasa Road",
        "+254700000105",
        True,
        "34 reviews - Instagram only",
        False,
    ),
    (
        # A landline: call only, never WhatsApp. Kept from the real list's mix.
        "Baraka Chemist",
        "Pharmacies and chemists",
        "Ngong Road",
        "+254700000106",
        False,
        "landline only - no website listed",
        False,
    ),
    (
        "Tumaini Legal Advocates",
        "Legal services",
        "Upper Hill",
        "+254700000107",
        True,
        "has a website, last updated 2021",
        True,
    ),
    (
        # No phone yet: exactly what the importer will hit in block 3.
        "Nairobi Bee Supplies",
        None,
        "Kasarani",
        None,
        False,
        "no phone number on the listing",
        False,
    ),
)


def build_sample_leads() -> list[Lead]:
    """Fresh ORM instances on every call, so a runner never shares state."""
    leads: list[Lead] = []
    activity_number = 0

    for index, (
        business_name,
        sector,
        area,
        phone,
        whatsapp_capable,
        website_status,
        has_website,
    ) in enumerate(SAMPLE_LEADS):
        created_at = SEED_START.replace(minute=index)
        lead = Lead(
            id=_seed_id(index + 1),
            business_name=business_name,
            sector=sector,
            area=area,
            phone=phone,
            whatsapp_capable=whatsapp_capable,
            website_status=website_status,
            has_website=has_website,
            source=SOURCE,
            # Nothing in Epic 1 moves a lead off "new" — nothing sends yet.
            status=LeadStatus.NEW,
            created_at=created_at,
            updated_at=created_at,
        )

        activity_number += 1
        lead.activity.append(
            Activity(
                id=_activity_id(activity_number),
                type="lead.created",
                actor="system",
                summary="Imported from the Google Maps list",
                created_at=created_at,
            )
        )

        activity_number += 1
        lead.activity.append(
            Activity(
                id=_activity_id(activity_number),
                type="lead.researched",
                actor="system",
                summary=f"Website research recorded: {website_status}",
                created_at=created_at.replace(second=30),
            )
        )

        leads.append(lead)

    return leads
