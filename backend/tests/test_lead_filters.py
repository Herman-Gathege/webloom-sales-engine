"""Backend Lead Desk filters, sorting, and filtered pagination."""

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ImportBatch, Lead, LeadProvenance, Suppression
from app.repositories import LeadRepository
from app.services.compliance_evaluator import ComplianceEvaluator
from app.services.contact_identity import contact_fingerprint


def add_provenance(lead: Lead, *, batch_id=None, source_name="Synthetic directory"):
    lead.provenance = LeadProvenance(
        import_batch_id=batch_id,
        source_name=source_name,
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
    record.evidence_summary = "Synthetic evidence for a requested website quote."
    record.evidence_source = "Synthetic inbound request"
    record.intended_purpose = "Website proposal"
    record.contact_context = "The named owner asked for a quote"
    record.reviewer = "reviewer@example.test"
    record.reviewed_at = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
    record.rationale = "The recorded request supports this outreach."
    record.reviewed_input_fingerprint = evaluator.channel_input_fingerprint(lead, "email")


def test_compliance_filters_combine_with_existing_lead_filters(
    client: TestClient, session: Session, make_lead
) -> None:
    eligible = make_lead(
        business_name="Eligible Optician",
        sector="Opticians and eyewear",
        area="Westlands",
        email="eligible@example.test",
    )
    add_provenance(eligible)
    approve_email(eligible)

    review = make_lead(
        business_name="Review Dentist",
        sector="Dental clinics",
        area="Westlands",
        email="review@example.test",
    )
    add_provenance(review)

    invalid = make_lead(
        business_name="Invalid Business",
        sector="Opticians and eyewear",
        area="CBD",
        phone=None,
        email=None,
    )
    add_provenance(invalid)

    session.add_all([eligible, review, invalid])
    session.flush()
    evaluator = ComplianceEvaluator(LeadRepository(session))
    for lead in (eligible, review, invalid):
        evaluator.evaluate(lead)

    response = client.get(
        "/api/v1/leads",
        params={
            "compliance_status": "eligible",
            "sector": "Opticians and eyewear",
            "area": "Westlands",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["business_name"] for item in body["items"]] == ["Eligible Optician"]
    assert body["items"][0]["compliance"]["status"] == "eligible"
    assert body["items"][0]["compliance"]["outreach_ready"] is True


def test_batch_provenance_and_suppression_audit_filters(
    client: TestClient, session: Session, make_lead
) -> None:
    batch = ImportBatch(filename="synthetic-batch.csv", row_count=2, accepted=2)
    session.add(batch)
    session.flush()

    imported = make_lead(
        business_name="Imported Review",
        email="imported@example.test",
        source="synthetic_batch",
    )
    add_provenance(imported, batch_id=batch.id, source_name="Synthetic batch")

    suppressed = make_lead(
        business_name="Suppressed Audit",
        email="suppressed@example.test",
    )
    add_provenance(suppressed)
    missing = make_lead(business_name="Missing Provenance")

    session.add_all([imported, suppressed, missing])
    session.flush()
    session.add(
        Suppression(
            lead_id=suppressed.id,
            contact_fingerprint=contact_fingerprint("email", suppressed.email),
            contact_kind="email",
            scope="email",
            reason="objection",
            source="Synthetic reply",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()
    evaluator = ComplianceEvaluator(LeadRepository(session))
    for lead in (imported, suppressed, missing):
        evaluator.evaluate(lead, force=True)

    by_batch = client.get(
        "/api/v1/leads",
        params={"batch_id": str(batch.id), "compliance_status": "needs_review"},
    )
    missing_source = client.get(
        "/api/v1/leads", params={"provenance": "missing"}
    )
    suppressed_rows = client.get(
        "/api/v1/leads", params={"has_suppression": "true"}
    )

    assert [row["business_name"] for row in by_batch.json()["items"]] == [
        "Imported Review"
    ]
    assert [row["business_name"] for row in missing_source.json()["items"]] == [
        "Missing Provenance"
    ]
    assert [row["business_name"] for row in suppressed_rows.json()["items"]] == [
        "Suppressed Audit"
    ]
    assert suppressed_rows.json()["items"][0]["compliance"]["suppressed_channels"] == [
        "email"
    ]


def test_search_sort_and_pagination_use_the_filtered_count(
    client: TestClient, session: Session, make_lead
) -> None:
    started = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)
    leads = []
    for index in range(5):
        lead = make_lead(
            business_name=f"Westlands Business {index}",
            area="Westlands",
            sector="Professional services",
            email=f"westlands-{index}@example.test",
            created_at=started + timedelta(minutes=index),
            updated_at=started + timedelta(minutes=index),
        )
        add_provenance(lead)
        leads.append(lead)
    unrelated = make_lead(business_name="Karen Business", area="Karen")
    add_provenance(unrelated)
    session.add_all([*leads, unrelated])
    session.flush()
    evaluator = ComplianceEvaluator(LeadRepository(session))
    for lead in [*leads, unrelated]:
        evaluator.evaluate(lead)

    response = client.get(
        "/api/v1/leads",
        params={
            "q": "westlands",
            "compliance_status": "needs_review",
            "sort": "business_name",
            "limit": 2,
            "offset": 2,
        },
    )

    body = response.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert [row["business_name"] for row in body["items"]] == [
        "Westlands Business 2",
        "Westlands Business 3",
    ]


def test_filter_options_are_real_database_values(
    client: TestClient, session: Session, make_lead
) -> None:
    batch = ImportBatch(filename="synthetic-options.csv", row_count=1, accepted=1)
    session.add(batch)
    session.flush()
    lead = make_lead(
        sector="Opticians and eyewear",
        area="Westlands",
        source="google_maps",
    )
    add_provenance(lead, batch_id=batch.id)
    session.add(lead)
    session.flush()
    ComplianceEvaluator(LeadRepository(session)).evaluate(lead)

    body = client.get("/api/v1/leads/filter-options").json()

    assert body["sectors"] == ["Opticians and eyewear"]
    assert body["areas"] == ["Westlands"]
    assert body["sources"] == ["google_maps"]
    assert body["compliance_statuses"] == [
        "eligible",
        "needs_review",
        "blocked",
        "invalid",
    ]
    assert body["import_batches"][0]["filename"] == "synthetic-options.csv"
