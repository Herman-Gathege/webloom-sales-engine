"""CSV import creates durable automatic compliance outcomes and honest counts."""

import csv
import io
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lead, LeadComplianceEvaluation, Suppression
from app.repositories import LeadRepository
from app.services.contact_identity import contact_fingerprint
from app.services.lead_import import LeadImportService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_clean_import_is_saved_as_needs_review_with_actual_summary_counts(
    session: Session,
) -> None:
    result = LeadImportService(LeadRepository(session)).import_file(
        (FIXTURES / "import_clean.csv").read_bytes(),
        "import_clean.csv",
    )

    assert (
        result.row_count,
        result.created,
        result.accepted,
        result.rejected,
        result.matched,
        result.duplicates,
        result.eligible,
        result.needs_review,
        result.blocked,
        result.invalid,
    ) == (3, 3, 3, 0, 0, 0, 0, 3, 0, 0)
    assert result.requiring_review == 3
    assert len(result.review_rows) == 3
    assert {row.compliance_status for row in result.review_rows} == {"needs_review"}
    assert session.scalar(select(func.count()).select_from(LeadComplianceEvaluation)) == 3
    assert all(lead.compliance is not None for lead in session.scalars(select(Lead)))
    assert all(
        lead.provenance is not None and lead.provenance.source_name == "Google Maps listing"
        for lead in session.scalars(select(Lead))
    )


def test_mixed_import_reports_duplicate_invalid_and_review_rows_separately(
    session: Session,
) -> None:
    result = LeadImportService(LeadRepository(session)).import_file(
        (FIXTURES / "import_mixed.csv").read_bytes(),
        "import_mixed.csv",
    )

    assert result.created == 3
    assert result.matched == 0
    assert result.duplicates == 1
    assert result.needs_review == 3
    assert result.invalid == 3
    assert result.blocked == 0
    assert {row.code for row in result.refused} == {
        "blank_business_name",
        "missing_phone",
        "unparseable_phone",
        "duplicate_phone",
    }
    assert {row.row for row in result.review_rows} == {2, 4, 8}


def test_an_existing_phone_is_reported_as_matched_without_overwriting(
    session: Session, make_lead
) -> None:
    existing = make_lead(
        business_name="Existing Synthetic Business",
        phone="+254700999001",
    )
    session.add(existing)
    session.flush()

    result = LeadImportService(LeadRepository(session)).import_file(
        (FIXTURES / "import_duplicate_of_existing.csv").read_bytes(),
        "duplicate.csv",
    )

    assert (result.created, result.matched, result.duplicates) == (0, 1, 1)
    session.refresh(existing)
    assert existing.business_name == "Existing Synthetic Business"
    assert session.scalar(select(func.count()).select_from(Lead)) == 1


def test_blocked_refusal_appears_in_the_actual_import_summary(session: Session) -> None:
    session.add(
        Suppression(
            contact_fingerprint=contact_fingerprint("phone", "+254700000901"),
            contact_kind="phone",
            scope="all_marketing",
            reason="opt_out",
            source="Synthetic written request",
            recorded_by="reviewer@example.test",
        )
    )
    session.flush()
    content = _csv(
        {
            "Business": "Synthetic Suppressed Business",
            "Sector": "Professional services",
            "Area": "Nairobi",
            "Phone": "0700 000901",
            "WhatsApp capable": "Yes",
            "Website status": "No website listed",
            "Source": "Google Maps listing",
        }
    )

    result = LeadImportService(LeadRepository(session)).import_file(
        content,
        "suppressed.csv",
    )

    assert result.created == 0
    assert result.rejected == 1
    assert result.blocked == 1
    assert result.refused[0].code == "suppressed_contact"


def test_import_normalises_whitespace_before_evaluation(session: Session) -> None:
    content = _csv(
        {
            "Business": "  Synthetic   Spaced Business  ",
            "Sector": "  Professional   services ",
            "Area": "  Westlands   Nairobi ",
            "Phone": "0700 000902",
            "WhatsApp capable": "Yes",
            "Website status": "No   website listed",
            "Source": "Google    Maps listing",
        }
    )

    result = LeadImportService(LeadRepository(session)).import_file(
        content,
        "spaced.csv",
    )

    lead = session.scalar(select(Lead))
    assert result.created == 1
    assert lead is not None
    assert lead.business_name == "Synthetic Spaced Business"
    assert lead.sector == "Professional services"
    assert lead.area == "Westlands Nairobi"
    assert lead.provenance is not None
    assert lead.provenance.source_name == "Google Maps listing"


def _csv(row: dict[str, str]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return buffer.getvalue().encode()
