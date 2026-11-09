"""Policy eligibility integrated with the durable compliance evaluator."""

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import LeadProvenance, LeadStatus, Suppression
from app.repositories import LeadRepository
from app.services.compliance_evaluator import ComplianceEvaluator
from app.services.compliance_policy import CompliancePolicy, CompliancePolicyRegistry
from app.services.contact_identity import contact_fingerprint
from app.services.outreach_gate import OutreachGateService


def policy(*, enabled: bool = True) -> CompliancePolicy:
    return CompliancePolicy(
        id="synthetic-email-policy",
        version="1",
        channel="email",
        source="google_maps",
        intended_purpose="Business outreach",
        contact_types=frozenset({"generic_business"}),
        collection_methods=frozenset({"Manual listing review"}),
        required_provenance_fields=frozenset(
            {
                "source",
                "source_name",
                "source_url",
                "collection_date",
                "collection_method",
                "intended_purpose",
                "contact_type",
            }
        ),
        lawful_basis="legitimate_interests",
        rationale="Synthetic test policy only.",
        approved_by="compliance@example.test",
        approved_at=date(2026, 11, 9),
        approval_reference="SYNTHETIC-ONLY",
        enabled=enabled,
    )


def registry(version: str = "1", *, enabled: bool = True) -> CompliancePolicyRegistry:
    return CompliancePolicyRegistry(
        version=version,
        policies=(policy(enabled=enabled),),
    )


def add_provenance(lead) -> None:
    lead.provenance = LeadProvenance(
        source_name="Google Maps listing",
        source_url="https://example.test/business",
        collection_date=date(2026, 11, 1),
        collection_method="Manual listing review",
        intended_purpose="Business outreach",
        contact_type="generic_business",
    )


def evaluator(session: Session, policies: CompliancePolicyRegistry) -> ComplianceEvaluator:
    return ComplianceEvaluator(
        LeadRepository(session),
        policy_registry=policies,
    )


def test_matching_policy_makes_one_channel_eligible_without_fake_human_review(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()

    evaluation = evaluator(session, registry()).evaluate(lead)

    assert evaluation.status == "eligible"
    assert evaluation.eligible_channels == ["email"]
    email_result = evaluation.channel_results[0]
    assert email_result["status"] == "eligible"
    assert email_result["decision_type"] == "automated_policy"
    assert email_result["policy_id"] == "synthetic-email-policy"
    assert email_result["policy_version"] == "1"
    assert email_result["decision_current"] is True
    assert len(email_result["input_fingerprint"]) == 64
    email_review = next(row for row in lead.eligibility if row.channel == "email")
    assert email_review.state == "needs_review"
    assert email_review.reviewer is None
    assert email_review.reviewed_at is None


def test_explicit_human_review_hold_blocks_an_otherwise_matching_policy(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    policies = registry()
    service = evaluator(session, policies)
    session.add(lead)
    session.flush()
    email_review = next(row for row in lead.eligibility if row.channel == "email")
    email_review.reviewer = "reviewer@example.test"
    email_review.reviewed_at = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
    email_review.rationale = "Hold this channel for a person to inspect."
    email_review.reviewed_input_fingerprint = service.channel_input_fingerprint(
        lead, "email"
    )

    evaluation = service.evaluate(lead)

    assert evaluation.status == "needs_review"
    email_result = evaluation.channel_results[0]
    assert email_result["decision_type"] == "human_review"
    assert email_result["decision_current"] is True
    assert "human_review_hold:email" in email_result["reason_codes"]


def test_all_marketing_suppression_overrides_automatic_policy(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()
    session.add(
        Suppression(
            lead_id=lead.id,
            contact_fingerprint=contact_fingerprint("email", lead.email),
            contact_kind="email",
            scope="all_marketing",
            reason="opt_out",
            source="Synthetic written request",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()

    evaluation = evaluator(session, registry()).evaluate(lead, force=True)

    assert evaluation.status == "blocked"
    email_result = evaluation.channel_results[0]
    assert email_result["status"] == "blocked"
    assert email_result["decision_type"] == "none"
    assert email_result["decision_current"] is False
    assert email_result["policy_id"] is None


def test_channel_suppression_does_not_hide_another_policy_eligible_channel(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()
    session.add(
        Suppression(
            lead_id=lead.id,
            contact_fingerprint=contact_fingerprint("phone", lead.phone),
            contact_kind="phone",
            scope="sms",
            reason="opt_out",
            source="Synthetic SMS request",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()

    evaluation = evaluator(session, registry()).evaluate(lead, force=True)

    assert evaluation.status == "eligible"
    assert evaluation.eligible_channels == ["email"]
    assert "sms" in evaluation.suppressed_channels
    assert evaluation.channel_results[1]["status"] == "blocked"


def test_lead_opt_out_blocks_a_policy_eligible_channel(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test", status=LeadStatus.OPTED_OUT)
    add_provenance(lead)
    session.add(lead)
    session.flush()

    evaluation = evaluator(session, registry()).evaluate(lead)

    assert evaluation.status == "blocked"
    email_result = evaluation.channel_results[0]
    assert email_result["status"] == "blocked"
    assert "lead_opted_out" in email_result["reason_codes"]


def test_policy_version_change_invalidates_a_reused_evaluation(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()
    first = evaluator(session, registry("1")).evaluate(lead)
    assert first.status == "eligible"

    second = evaluator(session, registry("2", enabled=False)).evaluate(lead)

    assert second.status == "needs_review"
    assert second.rule_version != "2026-10-27.1"
    assert "no_approved_policy:email" in second.reason_codes


def test_changed_provenance_invalidates_an_automated_policy_decision(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()
    service = evaluator(session, registry())
    first = service.evaluate(lead)
    assert first.status == "eligible"

    lead.provenance.intended_purpose = "Recruitment"
    session.flush()
    second = service.evaluate(lead)

    assert second.status == "needs_review"
    assert "policy_context_not_met:email" in second.reason_codes
    assert second.channel_results[0]["decision_type"] == "none"


def test_matching_policy_can_replace_a_stale_human_approval(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    service = evaluator(session, registry())
    session.add(lead)
    session.flush()
    email_review = next(row for row in lead.eligibility if row.channel == "email")
    email_review.state = "eligible"
    email_review.lawful_basis = "legitimate_interests"
    email_review.evidence_summary = "Synthetic prior evidence."
    email_review.evidence_source = "Synthetic prior source"
    email_review.intended_purpose = "Business outreach"
    email_review.contact_context = "Synthetic prior context"
    email_review.reviewer = "reviewer@example.test"
    email_review.reviewed_at = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
    email_review.rationale = "Synthetic prior human approval."
    email_review.reviewed_input_fingerprint = service.channel_input_fingerprint(
        lead, "email"
    )
    assert service.evaluate(lead).channel_results[0]["decision_type"] == "human_review"

    lead.email = "new-owner@example.test"
    session.flush()
    evaluation = service.evaluate(lead)

    assert evaluation.status == "eligible"
    email_result = evaluation.channel_results[0]
    assert email_result["status"] == "eligible"
    assert email_result["decision_type"] == "automated_policy"
    assert "review_stale:email" in email_result["reason_codes"]


def test_lead_api_exposes_automated_decision_metadata(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()
    evaluator(session, registry()).evaluate(lead)
    session.flush()

    response = client.get(f"/api/v1/leads/{lead.id}")

    assert response.status_code == 200
    email_result = response.json()["compliance"]["channel_results"][0]
    assert email_result["decision_type"] == "automated_policy"
    assert email_result["policy_id"] == "synthetic-email-policy"
    assert email_result["policy_version"] == "1"
    assert email_result["policy_approved_by"] == "compliance@example.test"
    assert email_result["policy_approval_reference"] == "SYNTHETIC-ONLY"
    assert "source_url" in email_result["evidence_references"]
    assert len(email_result["input_fingerprint"]) == 64


def test_outreach_gate_allows_a_current_automated_policy_decision(
    session: Session, make_lead
) -> None:
    lead = make_lead(email="owner@example.test")
    add_provenance(lead)
    session.add(lead)
    session.flush()

    result = OutreachGateService(
        LeadRepository(session),
        policy_registry=registry(),
    ).check(str(lead.id), "email", actor="reviewer@example.test")

    assert result.allowed is True
    assert result.compliance_status == "eligible"


def test_exception_filter_finds_partially_eligible_leads(
    client: TestClient, session: Session, make_lead
) -> None:
    complete = make_lead(
        business_name="Complete Policy Lead",
        email="complete@example.test",
        phone="+254700000991",
        whatsapp_capable=True,
    )
    partial = make_lead(
        business_name="Partial Policy Lead",
        email="partial@example.test",
        phone="+254700000992",
        whatsapp_capable=True,
    )
    add_provenance(complete)
    add_provenance(partial)
    session.add_all([complete, partial])
    session.flush()
    all_channels = CompliancePolicyRegistry(
        version="synthetic-all-channels",
        policies=tuple(
            CompliancePolicy(
                id=f"synthetic-{channel}-policy",
                version="1",
                channel=channel,
                source="google_maps",
                intended_purpose="Business outreach",
                contact_types=frozenset({"generic_business"}),
                collection_methods=frozenset({"Manual listing review"}),
                required_provenance_fields=frozenset(
                    {"source", "source_url", "intended_purpose", "contact_type"}
                ),
                lawful_basis="legitimate_interests",
                rationale="Synthetic test policy only.",
                approved_by="compliance@example.test",
                approved_at=date(2026, 11, 9),
                approval_reference="SYNTHETIC-ONLY",
            )
            for channel in ("email", "sms", "whatsapp")
        ),
    )
    evaluator(session, all_channels).evaluate(complete)
    evaluator(session, registry()).evaluate(partial)

    response = client.get(
        "/api/v1/leads",
        params={"exception_review": "true"},
    )

    assert response.status_code == 200
    assert [row["business_name"] for row in response.json()["items"]] == [
        "Partial Policy Lead"
    ]

