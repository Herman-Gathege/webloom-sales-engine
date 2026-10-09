"""The sample data, and the promise that seeding twice changes nothing."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Activity, Lead, LeadStatus
from app.seed import build_sample_leads, seed_sample_leads
from app.seed.sample_data import SAMPLE_LEADS


def _counts(session: Session) -> tuple[int, int]:
    leads = session.scalar(select(func.count()).select_from(Lead))
    activity = session.scalar(select(func.count()).select_from(Activity))
    return leads or 0, activity or 0


def test_seeding_an_empty_database_creates_the_sample(session: Session) -> None:
    result = seed_sample_leads(session)

    assert result.leads_created == len(SAMPLE_LEADS)
    assert result.leads_skipped == 0
    assert result.activity_created == len(SAMPLE_LEADS) * 2
    assert _counts(session) == (len(SAMPLE_LEADS), len(SAMPLE_LEADS) * 2)


def test_seeding_twice_creates_nothing_new(session: Session) -> None:
    seed_sample_leads(session)
    before = _counts(session)

    second = seed_sample_leads(session)

    assert second.leads_created == 0
    assert second.activity_created == 0
    assert second.leads_skipped == len(SAMPLE_LEADS)
    assert _counts(session) == before


def test_seeded_leads_follow_the_contract(session: Session) -> None:
    seed_sample_leads(session)
    leads = session.scalars(select(Lead)).all()

    # Nothing in Epic 1 moves a lead off "new" — nothing sends yet.
    assert {lead.status for lead in leads} == {LeadStatus.NEW}
    assert all(lead.source.strip() for lead in leads)
    assert all(lead.business_name.strip() for lead in leads)
    # Synthetic contacts only: the reserved +2547000... range, never a real number.
    assert all(lead.phone is None or lead.phone.startswith("+2547000") for lead in leads)
    # The sample exercises the fields the first six leads leave alone.
    assert any(lead.phone is None for lead in leads)
    assert any(lead.has_website for lead in leads)
    assert any(not lead.whatsapp_capable for lead in leads)


def test_every_seeded_lead_has_its_own_activity(session: Session) -> None:
    seed_sample_leads(session)

    for lead in session.scalars(select(Lead)).all():
        assert [entry.type for entry in lead.activity] == ["lead.created", "lead.researched"]
        assert all(entry.actor == "system" for entry in lead.activity)
        assert all(entry.lead_id == lead.id for entry in lead.activity)


def test_build_sample_leads_is_stable(session: Session) -> None:
    """Two runs of the builder mean two identical sets, so ids never move."""
    first = build_sample_leads()
    second = build_sample_leads()

    assert [lead.id for lead in first] == [lead.id for lead in second]
    assert [lead.phone for lead in first] == [lead.phone for lead in second]


def test_seeded_leads_are_visible_through_the_api(client: TestClient, session: Session) -> None:
    seed_sample_leads(session)

    body = client.get("/api/v1/leads").json()

    assert body["total"] == len(SAMPLE_LEADS)
    assert len(body["items"]) == len(SAMPLE_LEADS)

    first = body["items"][0]
    detail = client.get(f"/api/v1/leads/{first['id']}").json()
    assert len(detail["activity"]) == 2
