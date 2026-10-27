"""Individual and bulk outreach eligibility gates."""

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Lead, LeadProvenance, LeadStatus
from app.repositories import LeadRepository
from app.services.compliance_evaluator import ComplianceEvaluator


def add_provenance(lead: Lead) -> None:
    lead.provenance = LeadProvenance(
        source_name="Synthetic directory",
        source_url="https://example.test/source",
        collection_date=date(2026, 10, 20),
        collection_method="Synthetic listing review",
        intended_purpose="Business outreach",
        contact_type="generic_business",
    )


def approve_email(lead: Lead) -> None:
    evaluator = ComplianceEvaluator()
    record = next(row for row in lead.eligibility if row.channel == "email")
    record.state = "eligible"
    record.lawful_basis = "legitimate_interests"
    record.evidence_summary = "Synthetic evidence records the relevant business request."
    record.evidence_source = "Synthetic inbound request"
    record.intended_purpose = "Website proposal"
    record.contact_context = "The owner asked for a website quote"
    record.reviewer = "reviewer@example.test"
    record.reviewed_at = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
    record.rationale = "The recorded request supports this outreach."
    record.reviewed_input_fingerprint = evaluator.channel_input_fingerprint(lead, "email")


def test_individual_gate_allows_only_a_current_eligible_review(
    client: TestClient, session: Session, make_lead
) -> None:
    eligible = make_lead(email="eligible@example.test")
    add_provenance(eligible)
    approve_email(eligible)
    review = make_lead(email="review@example.test")
    add_provenance(review)
    session.add_all([eligible, review])
    session.flush()
    evaluator = ComplianceEvaluator(LeadRepository(session))
    for lead in (eligible, review):
        evaluator.evaluate(lead)

    allowed = client.post(f"/api/v1/leads/{eligible.id}/outreach-check/email")
    blocked = client.post(f"/api/v1/leads/{review.id}/outreach-check/email")

    assert allowed.status_code == 200
    assert allowed.json()["allowed"] is True
    assert allowed.json()["compliance_status"] == "eligible"
    assert blocked.status_code == 200
    assert blocked.json()["allowed"] is False
    assert blocked.json()["compliance_status"] == "needs_review"
    assert "human_review_required:email" in blocked.json()["reason_codes"]


def test_bulk_gate_returns_a_result_for_every_lead(
    client: TestClient, session: Session, make_lead
) -> None:
    eligible = make_lead(email="eligible@example.test")
    add_provenance(eligible)
    approve_email(eligible)
    opted_out = make_lead(
        email="opted@example.test",
        status=LeadStatus.OPTED_OUT,
    )
    add_provenance(opted_out)
    review = make_lead(email="review@example.test")
    add_provenance(review)
    session.add_all([eligible, opted_out, review])
    session.flush()
    evaluator = ComplianceEvaluator(LeadRepository(session))
    for lead in (eligible, opted_out, review):
        evaluator.evaluate(lead)

    response = client.post(
        "/api/v1/leads/outreach-check",
        json={
            "lead_ids": [str(eligible.id), str(opted_out.id), str(review.id)],
            "channel": "email",
        },
    )

    assert response.status_code == 200
    results = {row["lead_id"]: row for row in response.json()["results"]}
    assert results[str(eligible.id)]["allowed"] is True
    assert results[str(opted_out.id)]["allowed"] is False
    assert results[str(opted_out.id)]["compliance_status"] == "blocked"
    assert results[str(review.id)]["allowed"] is False


def test_gate_rechecks_changed_contact_before_outreach(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="before@example.test")
    add_provenance(lead)
    approve_email(lead)
    session.add(lead)
    session.flush()
    ComplianceEvaluator(LeadRepository(session)).evaluate(lead)

    lead.email = "after@example.test"
    session.flush()
    response = client.post(f"/api/v1/leads/{lead.id}/outreach-check/email")

    assert response.status_code == 200
    assert response.json()["allowed"] is False
    assert response.json()["compliance_status"] == "needs_review"
    assert "review_stale:email" in response.json()["reason_codes"]


def test_gate_rejects_malformed_and_unknown_lead_ids(client: TestClient) -> None:
    malformed = client.post("/api/v1/leads/not-a-uuid/outreach-check/email")
    unknown = client.post(
        "/api/v1/leads/00000000-0000-4000-8000-000000000099/outreach-check/email"
    )

    assert malformed.status_code == 404
    assert unknown.status_code == 404
