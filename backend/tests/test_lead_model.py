"""The Lead model's constraints, against a real PostgreSQL database."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError, StatementError
from sqlalchemy.orm import Session

from app.models import Activity, Lead, LeadStatus


def test_status_defaults_to_new(session: Session, make_lead) -> None:
    lead = make_lead()
    lead.status = LeadStatus.NEW
    session.add(lead)
    session.flush()
    session.refresh(lead)

    assert lead.status is LeadStatus.NEW
    assert lead.whatsapp_capable is True
    assert lead.has_website is False
    assert isinstance(lead.id, uuid.UUID)
    assert lead.created_at is not None and lead.updated_at is not None


def test_id_and_timestamps_are_filled_in_by_the_database(session: Session) -> None:
    lead = Lead(business_name="No defaults given", source="referral")
    session.add(lead)
    session.flush()
    session.refresh(lead)

    assert lead.id is not None
    assert lead.status is LeadStatus.NEW
    assert lead.created_at.tzinfo is not None
    assert lead.updated_at >= lead.created_at


@pytest.mark.parametrize(
    ("field", "value"),
    [("business_name", ""), ("source", "")],
)
def test_blank_required_text_is_rejected(
    session: Session, make_lead, field: str, value: str
) -> None:
    session.add(make_lead(**{field: value}))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_source_is_required(session: Session, make_lead) -> None:
    session.add(make_lead(source=None))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_phone_may_be_null_and_two_phone_less_leads_coexist(session: Session, make_lead) -> None:
    session.add(make_lead(phone=None))
    session.add(make_lead(phone=None))
    session.flush()

    assert len(session.scalars(select(Lead)).all()) == 2


def test_the_same_phone_twice_is_rejected(session: Session, make_lead) -> None:
    """Phone is the contract's de-duplication key, so the database enforces it."""
    session.add(make_lead(phone="+254700999001"))
    session.flush()

    session.add(make_lead(phone="+254700999001"))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_an_unknown_status_is_rejected(session: Session, make_lead) -> None:
    session.add(make_lead(status="probably"))
    with pytest.raises((IntegrityError, DBAPIError, StatementError)):
        session.flush()
    session.rollback()


def test_deleting_a_lead_removes_its_activity(session: Session, make_lead) -> None:
    lead = make_lead()
    lead.activity.append(
        Activity(type="lead.created", actor="system", summary="Imported from a list")
    )
    session.add(lead)
    session.flush()
    lead_id = lead.id

    session.delete(lead)
    session.flush()

    assert session.get(Lead, lead_id) is None
    remaining = session.scalars(select(Activity).where(Activity.lead_id == lead_id)).all()
    assert remaining == []


def test_activity_is_ordered_oldest_first(session: Session, make_lead) -> None:
    lead = make_lead()
    started = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
    lead.activity.append(
        Activity(
            type="lead.researched",
            actor="system",
            summary="Website research recorded",
            created_at=started + timedelta(minutes=5),
        )
    )
    lead.activity.append(
        Activity(
            type="lead.created",
            actor="system",
            summary="Imported from the Google Maps list",
            created_at=started,
        )
    )
    session.add(lead)
    session.flush()
    session.refresh(lead)

    assert [entry.type for entry in lead.activity] == ["lead.created", "lead.researched"]
