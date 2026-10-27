"""Automatic compliance evaluation, durable reuse, and stale-input handling."""

from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    LeadComplianceEvaluation,
    LeadProvenance,
    LeadStatus,
    Suppression,
)
from app.repositories import LeadRepository
from app.services.compliance_evaluator import ComplianceEvaluator
from app.services.contact_identity import contact_fingerprint


def add_provenance(lead, *, source_name: str = "Synthetic source") -> None:
    lead.provenance = LeadProvenance(
        source_name=source_name,
        source_url="https://example.test/source",
        collection_date=date(2026, 10, 20),
        collection_method="Synthetic listing review",
        intended_purpose="Business outreach",
        contact_type="generic_business",
    )


def approve(lead, channel: str = "email") -> None:
    evaluator = ComplianceEvaluator()
    record = next(row for row in lead.eligibility if row.channel == channel)
    record.state = "eligible"
    record.lawful_basis = "legitimate_interests"
    record.evidence_summary = "Synthetic evidence recorded for this test."
    record.evidence_source = "Synthetic inbound request"
    record.intended_purpose = "Website proposal"
    record.contact_context = "Named owner asked for a quote"
    record.reviewer = "reviewer@example.test"
    record.reviewed_at = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
    record.rationale = "The recorded context supports this channel review."
    record.reviewed_input_fingerprint = evaluator.channel_input_fingerprint(
        lead, channel
    )


def evaluate(session: Session, lead):
    session.add(lead)
    session.flush()
    evaluation = ComplianceEvaluator(LeadRepository(session)).evaluate(lead)
    session.flush()
    return evaluation


def test_a_current_complete_human_review_can_make_a_channel_eligible(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")

    evaluation = evaluate(session, lead)

    assert evaluation.status == "eligible"
    assert evaluation.data_quality_status == "complete"
    assert evaluation.outreach_ready is True
    assert evaluation.eligible_channels == ["email"]
    assert "eligible:email" in evaluation.reason_codes
    assert evaluation.channel_results[0]["decision_current"] is True


def test_missing_provenance_routes_a_potentially_usable_lead_to_review(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    approve(lead, "email")

    evaluation = evaluate(session, lead)

    assert evaluation.status == "needs_review"
    assert evaluation.data_quality_status == "incomplete"
    assert evaluation.outreach_ready is False
    assert "missing_provenance" in evaluation.reason_codes


def test_no_usable_contact_is_invalid(session: Session, make_lead) -> None:
    lead = make_lead(phone=None, email=None)
    add_provenance(lead)

    evaluation = evaluate(session, lead)

    assert evaluation.status == "invalid"
    assert evaluation.data_quality_status == "invalid"
    assert "no_usable_contact" in evaluation.reason_codes
    assert evaluation.outreach_ready is False


def test_lead_opt_out_is_blocked_and_cannot_be_outreach_ready(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test", status=LeadStatus.OPTED_OUT)
    add_provenance(lead)
    approve(lead, "email")

    evaluation = evaluate(session, lead)

    assert evaluation.status == "blocked"
    assert "lead_opted_out" in evaluation.reason_codes
    assert evaluation.outreach_ready is False


def test_terminal_suppression_wins_over_a_current_approval(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")
    session.add(lead)
    session.flush()
    session.add(
        Suppression(
            lead_id=lead.id,
            contact_fingerprint=contact_fingerprint("email", lead.email),
            contact_kind="email",
            scope="email",
            reason="objection",
            source="Synthetic reply",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()

    evaluation = ComplianceEvaluator(LeadRepository(session)).evaluate(
        lead, force=True
    )

    assert evaluation.status == "needs_review"
    assert "email" in evaluation.suppressed_channels
    assert evaluation.outreach_ready is False


def test_one_suppressed_channel_does_not_hide_another_eligible_channel(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")
    session.add(lead)
    session.flush()
    session.add(
        Suppression(
            lead_id=lead.id,
            contact_fingerprint=contact_fingerprint("phone", lead.phone),
            contact_kind="phone",
            scope="sms",
            reason="opt_out",
            source="Synthetic SMS opt-out",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()

    evaluation = ComplianceEvaluator(LeadRepository(session)).evaluate(
        lead, force=True
    )

    assert evaluation.status == "eligible"
    assert evaluation.eligible_channels == ["email"]
    assert evaluation.suppressed_channels == ["sms"]
    assert evaluation.outreach_ready is True


def test_unchanged_inputs_reuse_the_same_evaluation_and_audit_entry(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")
    evaluator = ComplianceEvaluator(LeadRepository(session))
    session.add(lead)
    session.flush()

    first = evaluator.evaluate(lead)
    session.flush()
    first_id = first.id
    first_time = first.evaluated_at
    audit_count = session.scalar(
        select(func.count())
        .select_from(Activity)
        .where(Activity.type == "lead.compliance_evaluated")
    )

    second = evaluator.evaluate(lead)

    assert second.id == first_id
    assert second.evaluated_at == first_time
    assert audit_count == 1
    assert (
        session.scalar(
            select(func.count())
            .select_from(Activity)
            .where(Activity.type == "lead.compliance_evaluated")
        )
        == 1
    )


def test_contact_change_makes_prior_approval_stale_without_erasing_it(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")
    evaluator = ComplianceEvaluator(LeadRepository(session))
    session.add(lead)
    session.flush()
    first = evaluator.evaluate(lead)
    original_review_fingerprint = next(
        row.reviewed_input_fingerprint
        for row in lead.eligibility
        if row.channel == "email"
    )
    assert first.status == "eligible"

    lead.email = "changed@example.test"
    session.flush()
    second = evaluator.evaluate(lead, force=True)

    assert second.status == "needs_review"
    assert "review_stale:email" in second.reason_codes
    human_decision = next(row for row in lead.eligibility if row.channel == "email")
    assert human_decision.state == "eligible"
    assert human_decision.reviewed_input_fingerprint == original_review_fingerprint
    assert session.scalar(select(func.count()).select_from(LeadComplianceEvaluation)) == 1


def test_provenance_change_also_makes_a_prior_approval_stale(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")
    evaluator = ComplianceEvaluator(LeadRepository(session))
    session.add(lead)
    session.flush()
    assert evaluator.evaluate(lead).status == "eligible"

    lead.provenance.source_url = "https://example.test/different-source"
    session.flush()
    evaluation = evaluator.evaluate(lead, force=True)

    assert evaluation.status == "needs_review"
    assert "review_stale:email" in evaluation.reason_codes


def test_provenance_change_makes_prior_approval_stale(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "email")
    evaluator = ComplianceEvaluator(LeadRepository(session))
    session.add(lead)
    session.flush()
    assert evaluator.evaluate(lead).status == "eligible"

    assert lead.provenance is not None
    lead.provenance.source_name = "Changed synthetic source"
    session.flush()
    evaluation = evaluator.evaluate(lead, force=True)

    assert evaluation.status == "needs_review"
    assert "review_stale:email" in evaluation.reason_codes
    assert next(row for row in lead.eligibility if row.channel == "email").state == "eligible"


def test_a_suppression_on_one_channel_does_not_make_another_approval_stale(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    approve(lead, "sms")
    session.add(lead)
    session.flush()
    session.add(
        Suppression(
            lead_id=lead.id,
            contact_fingerprint=contact_fingerprint("email", lead.email),
            contact_kind="email",
            scope="email",
            reason="objection",
            source="Synthetic email reply",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()

    evaluation = ComplianceEvaluator(LeadRepository(session)).evaluate(
        lead, force=True
    )

    assert evaluation.status == "eligible"
    assert evaluation.eligible_channels == ["sms"]
    assert evaluation.suppressed_channels == ["email"]
    assert evaluation.outreach_ready is True
