"""Compliance provenance, human review, and terminal suppression behavior."""

import csv
import io
import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Activity, ImportBatch, Lead, LeadProvenance, Suppression
from app.repositories import LeadRepository
from app.services.lead_import import LeadImportService

HEADER = [
    "Date added",
    "Business",
    "Sector",
    "Area",
    "Phone",
    "WhatsApp capable",
    "Website status",
    "Source",
    "Email",
    "Contact name",
    "Contact type",
    "Source URL",
    "Collection date",
    "Collection method",
    "Intended purpose",
]


def csv_upload(**overrides: str) -> bytes:
    row = {
        "Date added": "2026-09-23",
        "Business": "Synthetic Compliance Business",
        "Sector": "Professional services",
        "Area": "Nairobi",
        "Phone": "0700 000901",
        "WhatsApp capable": "Yes",
        "Website status": "No website listed",
        "Source": "Google Maps listing",
        "Email": "owner@example.test",
        "Contact name": "Synthetic Owner",
        "Contact type": "named individual",
        "Source URL": "https://example.test/business/901",
        "Collection date": "2026-09-20",
        "Collection method": "Manual listing review",
        "Intended purpose": "Business outreach",
    }
    row.update(overrides)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HEADER)
    writer.writeheader()
    writer.writerow(row)
    return buffer.getvalue().encode()


def upload(client: TestClient, **overrides: str):
    return client.post(
        "/api/v1/leads/import",
        files={"file": ("compliance.csv", csv_upload(**overrides), "text/csv")},
    )


def review_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "state": "eligible",
        "lawful_basis": "legitimate_interests",
        "evidence_summary": "Business owner asked for a website quote by email.",
        "evidence_source": "Inbound email held by sales",
        "intended_purpose": "Website proposal follow-up",
        "contact_context": "Named business owner contacted us first",
        "reviewer": "Anne",
        "rationale": "Direct request and relevant business context are recorded.",
    }
    payload.update(overrides)
    return payload


def test_import_persists_provenance_batch_and_three_pending_channels(
    client: TestClient, session: Session
) -> None:
    response = upload(client)

    assert response.status_code == 200
    summary = response.json()
    assert summary["accepted"] == 1
    assert summary["requiring_review"] == 1
    assert summary["duplicates"] == 0

    lead = session.scalar(select(Lead))
    assert lead is not None
    assert lead.email == "owner@example.test"
    provenance = session.scalar(select(LeadProvenance))
    assert provenance is not None
    assert provenance.row_number == 2
    assert provenance.source_url == "https://example.test/business/901"
    assert str(provenance.collection_date) == "2026-09-20"
    assert provenance.collection_method == "Manual listing review"
    assert provenance.intended_purpose == "Business outreach"
    assert provenance.contact_type == "named_individual"
    assert {row.channel: row.state for row in lead.eligibility} == {
        "email": "needs_review",
        "sms": "needs_review",
        "whatsapp": "needs_review",
    }
    assert session.scalar(select(func.count()).select_from(ImportBatch)) == 1


def test_missing_optional_fields_import_as_reviewable_records(
    client: TestClient, session: Session
) -> None:
    response = client.post(
        "/api/v1/leads/import",
        files={
            "file": (
                "legacy.csv",
                csv_upload(
                    Email="",
                    **{
                        "Contact name": "",
                        "Contact type": "",
                        "Source URL": "",
                        "Collection date": "",
                        "Collection method": "",
                        "Intended purpose": "",
                    },
                ),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    lead = session.scalar(select(Lead))
    assert lead is not None
    assert lead.email is None
    assert {row.effective_state for row in lead.eligibility} == {"needs_review"}
    assert lead.provenance is not None
    # Collection date falls back to the existing `Date added` value.
    assert str(lead.provenance.collection_date) == "2026-09-23"
    assert lead.provenance.collection_method == "Google Maps listing"


def test_invalid_optional_values_warn_but_do_not_refuse_the_lead(
    client: TestClient, session: Session
) -> None:
    response = upload(
        client,
        Email="not-an-email",
        **{
            "Contact type": "department robot",
            "Source URL": "javascript:alert(1)",
            "Collection date": "20260920",
        },
    )

    body = response.json()
    assert body["accepted"] == 1
    assert {warning["code"] for warning in body["warnings"]} == {
        "email_invalid",
        "contact_type_unrecognised",
        "source_url_invalid",
        "collection_date_invalid",
    }
    assert "not-an-email" not in json.dumps(body)
    lead = session.scalar(select(Lead))
    assert lead is not None
    assert lead.email is None
    assert lead.provenance is not None
    assert lead.provenance.contact_type == "unknown"
    assert lead.provenance.source_url is None
    assert lead.provenance.collection_date is None


def test_an_all_refused_file_still_creates_an_import_batch(
    client: TestClient, session: Session
) -> None:
    response = upload(client, Business="")

    assert response.status_code == 200
    assert response.json()["accepted"] == 0
    batch = session.scalar(select(ImportBatch))
    assert batch is not None
    assert (batch.row_count, batch.accepted, batch.rejected) == (1, 0, 1)


def test_provenance_survives_review_and_suppression_updates(
    client: TestClient, session: Session
) -> None:
    upload(client)
    lead = session.scalar(select(Lead))
    assert lead is not None

    reviewed = client.put(
        f"/api/v1/leads/{lead.id}/eligibility/email",
        json=review_payload(),
    )
    assert reviewed.status_code == 200
    suppressed = client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "sms",
            "reason": "objection",
            "source": "Synthetic seller record",
            "recorded_by": "Anne",
        },
    )
    assert suppressed.status_code == 200

    provenance = suppressed.json()["provenance"]
    assert provenance["source_url"] == "https://example.test/business/901"
    assert provenance["collection_method"] == "Manual listing review"
    assert provenance["intended_purpose"] == "Business outreach"


def test_channel_reviews_are_independent_and_audited(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    session.add(lead)
    session.flush()

    response = client.put(
        f"/api/v1/leads/{lead.id}/eligibility/email",
        json=review_payload(),
    )

    assert response.status_code == 200
    states = {row["channel"]: row["effective_state"] for row in response.json()["eligibility"]}
    assert states == {
        "email": "eligible",
        "sms": "needs_review",
        "whatsapp": "needs_review",
    }
    audit = session.scalar(
        select(Activity).where(Activity.type == "lead.eligibility_reviewed")
    )
    assert audit is not None
    assert audit.actor == "Anne"
    assert audit.details == {
        "channel": "email",
        "previous_state": "needs_review",
        "new_state": "eligible",
        "lawful_basis": "legitimate_interests",
    }
    assert "owner@example.test" not in json.dumps(audit.details)


def test_a_public_listing_alone_starts_pending_and_eligible_requires_evidence(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    session.add(lead)
    session.flush()

    detail = client.get(f"/api/v1/leads/{lead.id}").json()
    assert {row["effective_state"] for row in detail["eligibility"]} == {"needs_review"}

    invalid = client.put(
        f"/api/v1/leads/{lead.id}/eligibility/sms",
        json={"state": "eligible", "reviewer": "Anne", "rationale": "Looks public"},
    )
    assert invalid.status_code == 422
    assert "Eligible reviews require" in json.dumps(invalid.json())


def test_channel_suppression_only_blocks_that_channel(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    session.add(lead)
    session.flush()

    response = client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "sms",
            "reason": "opt_out",
            "source": "Reply to pilot SMS",
            "recorded_by": "Anne",
            "note": "Asked for email only.",
        },
    )

    assert response.status_code == 200
    states = {row["channel"]: row["effective_state"] for row in response.json()["eligibility"]}
    assert states["sms"] == "suppressed"
    assert states["email"] == "needs_review"
    assert states["whatsapp"] == "needs_review"
    assert "contact_fingerprint" not in json.dumps(response.json())


def test_a_channel_suppression_requires_a_contact_for_that_channel(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(phone=None, email=None)
    session.add(lead)
    session.flush()

    response = client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "email",
            "reason": "opt_out",
            "source": "Written request",
            "recorded_by": "Anne",
        },
    )

    assert response.status_code == 409
    assert "no contact" in response.json()["detail"].lower()


def test_all_marketing_suppression_wins_everywhere_and_is_idempotent(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    session.add(lead)
    session.flush()
    payload = {
        "scope": "all_marketing",
        "reason": "opt_out",
        "source": "Written request",
        "recorded_by": "Anne",
        "note": "Do not contact this business again.",
    }

    first = client.post(f"/api/v1/leads/{lead.id}/suppressions", json=payload)
    second = client.post(f"/api/v1/leads/{lead.id}/suppressions", json=payload)

    assert first.status_code == second.status_code == 200
    assert {row["effective_state"] for row in second.json()["eligibility"]} == {
        "suppressed"
    }
    assert session.scalar(select(func.count()).select_from(Suppression)) == 2
    assert session.scalar(
        select(func.count())
        .select_from(Activity)
        .where(Activity.type == "lead.suppressed")
    ) == 1
    raw_audit = json.dumps(
        [activity.details for activity in session.scalars(select(Activity)).all()]
    )
    assert lead.phone not in raw_audit
    assert "owner@example.test" not in raw_audit


def test_a_suppressed_channel_cannot_be_reapproved(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    session.add(lead)
    session.flush()
    client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "email",
            "reason": "objection",
            "source": "Reply to pilot email",
            "recorded_by": "Anne",
        },
    )

    response = client.put(
        f"/api/v1/leads/{lead.id}/eligibility/email",
        json=review_payload(),
    )

    assert response.status_code == 409
    assert "Suppression is terminal" in response.json()["detail"]


def test_channel_suppression_survives_deletion_and_reimport(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(phone="+254700000901", email="owner@example.test")
    session.add(lead)
    session.flush()
    client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "sms",
            "reason": "opt_out",
            "source": "Reply to pilot SMS",
            "recorded_by": "Anne",
        },
    )
    session.delete(lead)
    session.flush()

    result = LeadImportService(LeadRepository(session)).import_file(
        csv_upload(), "channel-restriction.csv"
    )

    assert result.accepted == 1
    reimported = session.scalar(select(Lead))
    assert reimported is not None
    detail = client.get(f"/api/v1/leads/{reimported.id}").json()
    states = {row["channel"]: row["effective_state"] for row in detail["eligibility"]}
    assert states == {
        "email": "needs_review",
        "sms": "suppressed",
        "whatsapp": "needs_review",
    }


def test_whitespace_only_decision_fields_are_rejected(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    session.add(lead)
    session.flush()

    review = client.put(
        f"/api/v1/leads/{lead.id}/eligibility/email",
        json=review_payload(reviewer="   "),
    )
    suppression = client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "all_marketing",
            "reason": "opt_out",
            "source": " ",
            "recorded_by": "Anne",
        },
    )

    assert review.status_code == 422
    assert suppression.status_code == 422


def test_an_all_marketing_opt_out_blocks_a_fresh_import_and_survives_lead_deletion(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(phone="+254700000901", email="owner@example.test")
    session.add(lead)
    session.flush()
    client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "all_marketing",
            "reason": "opt_out",
            "source": "Written request",
            "recorded_by": "Anne",
        },
    )
    session.delete(lead)
    session.flush()

    result = LeadImportService(LeadRepository(session)).import_file(
        csv_upload(), "after-opt-out.csv"
    )

    assert result.accepted == 0
    assert [(row.code, row.row) for row in result.refused] == [("suppressed_contact", 2)]
    assert session.scalar(select(func.count()).select_from(Suppression)) == 2
