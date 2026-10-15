"""The importer's rules against the real database: what it saves, what it refuses.

This is the engine on its own; the endpoint that serves it is wired up in the next
pull request.

The fixtures are synthetic — reserved `+2547000...` numbers and invented names.
No test reads `data/`: that directory is gitignored, so such a test would pass
here and fail everywhere else (see `tests/fixtures/README.md`).
"""

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Activity, Lead, LeadStatus
from app.repositories import LeadRepository
from app.services.lead_import import ImportResult, LeadImportService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def import_fixture(session: Session, fixture: str) -> ImportResult:
    service = LeadImportService(LeadRepository(session))
    return service.import_file((FIXTURES / fixture).read_bytes(), fixture)


def lead_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Lead)) or 0


def test_the_clean_file_imports_every_row(session: Session) -> None:
    result = import_fixture(session, "import_clean.csv")

    assert (result.row_count, result.accepted, result.rejected) == (3, 3, 0)
    assert result.refused == []
    assert result.warnings == []


def test_an_imported_lead_carries_the_mapped_fields(session: Session) -> None:
    import_fixture(session, "import_clean.csv")

    leads = {lead.business_name: lead for lead in session.scalars(select(Lead)).all()}
    first = leads["Synthetic Opticians One"]
    landline = leads["Synthetic Chemist Three"]

    assert first.phone == "+254700000201"
    assert first.sector == "Opticians and eyewear"
    assert first.area == "CBD"
    assert first.whatsapp_capable is True
    assert first.website_status == "12 reviews - no website listed"
    assert first.has_website is False
    assert first.source == "google_maps"
    assert first.status == LeadStatus.NEW
    assert landline.phone == "+254200000203"
    assert landline.whatsapp_capable is False


def test_every_imported_lead_gets_the_same_two_entries_as_a_seeded_one(session: Session) -> None:
    import_fixture(session, "import_clean.csv")

    for lead in session.scalars(select(Lead)).all():
        assert [entry.type for entry in lead.activity] == ["lead.created", "lead.researched"]
        assert [entry.summary for entry in lead.activity] == [
            "Imported from the Google Maps list",
            f"Website research recorded: {lead.website_status}",
        ]
        assert all(entry.actor == "system" for entry in lead.activity)
        assert all(entry.lead_id == lead.id for entry in lead.activity)
    assert session.scalar(select(func.count()).select_from(Activity)) == 6


def test_the_files_first_row_becomes_the_newest_lead(session: Session) -> None:
    import_fixture(session, "import_clean.csv")

    items, total = LeadRepository(session).list_leads(limit=50, offset=0)

    assert total == 3
    assert [lead.business_name for lead in items] == [
        "Synthetic Opticians One",
        "Synthetic Agrovet Two",
        "Synthetic Chemist Three",
    ]


def test_the_bad_rows_are_refused_and_the_good_ones_land(session: Session) -> None:
    result = import_fixture(session, "import_mixed.csv")

    assert (result.row_count, result.accepted, result.rejected) == (7, 3, 4)
    assert [(row.row, row.code) for row in result.refused] == [
        (3, "blank_business_name"),
        (5, "unparseable_phone"),
        (6, "missing_phone"),
        (7, "duplicate_phone"),
    ]
    assert all(row.reason.strip() for row in result.refused)

    imported = {lead.business_name for lead in session.scalars(select(Lead)).all()}
    assert imported == {
        "Synthetic Mixed One",
        "Synthetic Mixed Landline",
        "Synthetic Mixed Unmapped",
    }


def test_the_duplicate_names_the_row_it_repeats(session: Session) -> None:
    result = import_fixture(session, "import_mixed.csv")

    duplicate = next(row for row in result.refused if row.code == "duplicate_phone")

    assert duplicate.row == 7
    assert duplicate.reason == "This phone number is already on row 2 of the file."
    # One lead holds that number, not two.
    holders = session.scalar(
        select(func.count()).select_from(Lead).where(Lead.phone == "+254700000301")
    )
    assert holders == 1


def test_a_warning_reports_a_value_and_never_refuses_the_row(session: Session) -> None:
    result = import_fixture(session, "import_mixed.csv")

    assert [(warning.row, warning.code) for warning in result.warnings] == [
        (8, "website_status_unclassified"),
    ]
    assert [warning.field for warning in result.warnings] == ["website_status"]
    assert all(warning.message.strip() for warning in result.warnings)

    unmapped = session.scalar(select(Lead).where(Lead.business_name == "Synthetic Mixed Unmapped"))
    assert unmapped is not None
    # A sector is stored exactly as written: the contract defers the controlled
    # vocabulary, so an empty one is simply empty rather than a warning.
    assert unmapped.sector is None
    assert unmapped.website_status == "listing unclear - check with owner"
    assert unmapped.has_website is False


def test_a_number_we_already_hold_is_refused(session: Session, make_lead) -> None:
    session.add(make_lead(phone="+254700999001"))
    session.flush()

    result = import_fixture(session, "import_duplicate_of_existing.csv")

    assert (result.row_count, result.accepted, result.rejected) == (1, 0, 1)
    assert result.refused[0].row == 2
    assert result.refused[0].code == "duplicate_phone"
    assert result.refused[0].reason == "This phone number is already in the system."
    assert lead_count(session) == 1


def test_only_a_row_that_imported_claims_its_phone(session: Session) -> None:
    """A refused row's number is not held, so the next row with it can still import."""
    content = (
        (FIXTURES / "import_clean.csv").read_bytes().split(b"\r\n", 1)[0]
        + b"\r\n"
        + b"2026-09-23,,Sector,Area,0700 000601,Yes,New listing - no website,,"
        + b"Google Maps listing,,,,,,,\r\n"
        + b"2026-09-23,Synthetic Second Claim,Sector,Area,0700 000601,Yes,"
        + b"New listing - no website,,Google Maps listing,,,,,,,\r\n"
    )

    result = LeadImportService(LeadRepository(session)).import_file(content, "inline.csv")

    assert (result.row_count, result.accepted, result.rejected) == (2, 1, 1)
    assert [(row.row, row.code) for row in result.refused] == [(2, "blank_business_name")]
    assert session.scalar(select(Lead).where(Lead.phone == "+254700000601")) is not None


def test_a_header_only_file_imports_nothing(session: Session) -> None:
    result = import_fixture(session, "import_header_only.csv")

    assert (result.row_count, result.accepted, result.rejected) == (0, 0, 0)
    assert result.refused == []
    assert lead_count(session) == 0


def test_importing_the_same_file_twice_creates_nothing_the_second_time(session: Session) -> None:
    import_fixture(session, "import_clean.csv")
    before = lead_count(session)

    second = import_fixture(session, "import_clean.csv")

    assert (second.accepted, second.rejected) == (0, 3)
    assert {row.code for row in second.refused} == {"duplicate_phone"}
    assert lead_count(session) == before == 3


def test_a_landline_that_claims_whatsapp_is_corrected_and_reported(session: Session) -> None:
    """The contract says a landline is never WhatsApp-capable, whatever the file says."""
    content = (
        (FIXTURES / "import_clean.csv").read_bytes().split(b"\r\n", 1)[0]
        + b"\r\n"
        + b"2026-09-23,Synthetic Confused Landline,Opticians and eyewear,CBD,020 0000701,"
        + b"Yes,New listing - no website,,Google Maps listing,,,,,,,\r\n"
    )

    result = LeadImportService(LeadRepository(session)).import_file(content, "inline.csv")

    assert result.accepted == 1
    assert [(warning.row, warning.code) for warning in result.warnings] == [
        (2, "landline_marked_whatsapp")
    ]
    confused = session.scalar(select(Lead).where(Lead.phone == "+254200000701"))
    assert confused is not None
    assert confused.whatsapp_capable is False


def test_an_unreadable_whatsapp_value_and_an_unknown_source_are_reported(session: Session) -> None:
    content = (
        (FIXTURES / "import_clean.csv").read_bytes().split(b"\r\n", 1)[0]
        + b"\r\n"
        + b"2026-09-23,Synthetic Maybe Mobile,Opticians and eyewear,CBD,0700 000801,Maybe,"
        + b"4 reviews - no website listed,,Referral from Anne,,,,,,,\r\n"
    )

    result = LeadImportService(LeadRepository(session)).import_file(content, "inline.csv")

    assert (result.accepted, result.rejected) == (1, 0)
    assert [(warning.row, warning.code) for warning in result.warnings] == [
        (2, "whatsapp_value_unrecognised"),
        (2, "source_unrecognised"),
    ]
    imported = session.scalar(select(Lead).where(Lead.phone == "+254700000801"))
    assert imported is not None
    # A mobile whose column we cannot read is treated as a mobile, and a source we
    # have not seen before is kept rather than dropped.
    assert imported.whatsapp_capable is True
    assert imported.source == "referral_from_anne"
