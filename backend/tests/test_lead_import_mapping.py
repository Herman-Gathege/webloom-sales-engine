"""The importer's pure helpers: the phone shapes, the website grammars, the source aliases.

Nothing here touches the database, so it runs anywhere and fails fast. The values
come from the real list's shapes, described in
`docs/research/2026-10-08-lead-list-audit.md`.
"""

from pathlib import Path

import pytest

from app.services.lead_import import (
    DUPLICATE_IN_FILE_REASON,
    ImportFileError,
    is_landline,
    map_row,
    normalise_phone,
    normalise_source,
    parse_website_status,
    read_rows,
    refusal_for,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def row(**overrides: str) -> dict[str, str]:
    """A valid row, exactly as `csv.DictReader` hands it over."""
    values = {
        "Business": "Synthetic Business",
        "Sector": "Opticians and eyewear",
        "Area": "CBD",
        "Phone": "0700 000201",
        "WhatsApp capable": "Yes",
        "Website status": "12 reviews - no website listed",
        "Source": "Google Maps listing",
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0700 000201", "+254700000201"),
        ("0700-000-201", "+254700000201"),
        ("(0700) 000201", "+254700000201"),
        ("020 0000203", "+254200000203"),
        ("+254 700 000201", "+254700000201"),
        ("+254700000201", "+254700000201"),
        ("0700000201", "+254700000201"),
    ],
)
def test_the_lists_phone_shapes_become_e164(raw: str, expected: str) -> None:
    assert normalise_phone(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "n/a", "0700 00020", "0700 0002011", "+254 700 0002012", "0712 34567x", "+1 202 555 0143"],
)
def test_a_phone_we_cannot_read_is_an_error_rather_than_a_guess(raw: str) -> None:
    with pytest.raises(ValueError):
        normalise_phone(raw)


@pytest.mark.parametrize(
    ("phone", "expected"),
    [
        ("+254200000203", True),  # Nairobi, 020
        ("+254410000000", True),  # Mombasa, 041
        ("+254700000201", False),  # mobile, 07…
        ("+254100000000", False),  # mobile, 01…
        ("+254", False),
        ("", False),
    ],
)
def test_landlines_are_told_apart_from_mobiles(phone: str, expected: bool) -> None:
    assert is_landline(phone) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("3,713 reviews - no website listed", (False, True)),
        ("1 review - no website listed", (False, True)),
        ("New listing - no website", (False, True)),
        ("No website listed", (False, True)),
        ("23 reviews - Facebook page only", (False, True)),
        ("26 reviews - Instagram only", (False, True)),
        ("has a website, last updated 2021", (True, True)),
        ("www.example.co.ke", (True, True)),
        ("http://example.co.ke", (True, True)),
        ("listing unclear - check with owner", (False, False)),
        ("", (False, False)),
    ],
)
def test_the_website_grammars(raw: str, expected: tuple[bool, bool]) -> None:
    assert parse_website_status(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Google Maps listing", ("google_maps", True)),
        ("google maps listing", ("google_maps", True)),
        ("Referral", ("referral", False)),
        ("Warm introduction from Anne", ("warm_introduction_from_anne", False)),
        ("", ("", False)),
        ("***", ("", False)),
    ],
)
def test_source_aliases_and_slugs(raw: str, expected: tuple[str, bool]) -> None:
    assert normalise_source(raw) == expected


def test_a_recognised_row_warns_about_nothing() -> None:
    mapped, warnings = map_row(2, row())

    assert warnings == []
    assert (mapped.business_name, mapped.phone, mapped.sector, mapped.area) == (
        "Synthetic Business",
        "+254700000201",
        "Opticians and eyewear",
        "CBD",
    )
    assert (mapped.whatsapp_capable, mapped.website_status, mapped.has_website) == (
        True,
        "12 reviews - no website listed",
        False,
    )
    assert mapped.source == "google_maps"


def test_a_landline_marked_call_only_is_not_whatsapp_capable() -> None:
    mapped, warnings = map_row(2, row(**{"Phone": "020 0000203", "WhatsApp capable": "Call only"}))

    assert mapped.phone == "+254200000203"
    assert mapped.whatsapp_capable is False
    assert warnings == []


@pytest.mark.parametrize("raw", ["maybe", "", "true", "y"])
def test_a_whatsapp_value_we_did_not_write_is_reported_and_derived(raw: str) -> None:
    """Only `Yes` and `Call only` are ours; anything else is worked out from the number."""
    mapped, warnings = map_row(2, row(**{"WhatsApp capable": raw}))

    assert mapped.whatsapp_capable is True
    assert [(warning.code, warning.field, warning.value) for warning in warnings] == [
        ("whatsapp_value_unrecognised", "whatsapp_capable", raw)
    ]


def test_an_unrecognised_whatsapp_value_on_a_landline_derives_call_only() -> None:
    mapped, _ = map_row(2, row(**{"Phone": "020 0000203", "WhatsApp capable": "maybe"}))

    assert mapped.whatsapp_capable is False


@pytest.mark.parametrize("sector", ["Underwater basket weaving", ""])
def test_a_sector_is_kept_as_written_and_never_reported(sector: str) -> None:
    """The contract defers any controlled vocabulary, so there is nothing to map against."""
    mapped, warnings = map_row(2, row(**{"Sector": sector}))

    assert mapped.sector == (sector or None)
    assert warnings == []
    assert refusal_for(2, row(**{"Sector": sector})) is None


def test_an_unclassified_website_status_keeps_the_raw_value() -> None:
    mapped, warnings = map_row(2, row(**{"Website status": "listing unclear - check with owner"}))

    assert mapped.website_status == "listing unclear - check with owner"
    assert mapped.has_website is False
    assert [warning.code for warning in warnings] == ["website_status_unclassified"]


def test_a_new_source_is_slugified_and_reported() -> None:
    mapped, warnings = map_row(2, row(**{"Source": "Referral"}))

    assert mapped.source == "referral"
    assert [(warning.code, warning.field, warning.value) for warning in warnings] == [
        ("source_unrecognised", "source", "Referral")
    ]


@pytest.mark.parametrize("source", ["", "   ", "***"])
def test_a_row_we_cannot_attribute_is_refused(source: str) -> None:
    refusal = refusal_for(2, row(**{"Source": source}))

    assert refusal is not None
    assert refusal.code == "blank_source"
    assert refusal.reason


def test_refusals_are_checked_in_a_fixed_order() -> None:
    """A row with several problems always reports the same one, so the report is stable."""
    refusal = refusal_for(2, row(**{"Business": "", "Phone": "", "Source": ""}))

    assert refusal is not None
    assert refusal.code == "blank_business_name"
    assert refusal.row == 2


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"Business": ""}, "blank_business_name"),
        ({"Phone": ""}, "missing_phone"),
        ({"Phone": "n/a"}, "unparseable_phone"),
        ({"Source": ""}, "blank_source"),
    ],
)
def test_each_refusal_has_a_code_and_a_reason_a_person_reads(
    overrides: dict[str, str], code: str
) -> None:
    refusal = refusal_for(7, row(**overrides))

    assert refusal is not None
    assert (refusal.row, refusal.code) == (7, code)
    assert refusal.reason.strip() != ""


def test_the_duplicate_reason_names_the_row_it_repeats() -> None:
    reason = DUPLICATE_IN_FILE_REASON.format(row=3)

    assert reason == "This phone number is already on row 3 of the file."


def test_rows_are_numbered_the_way_a_spreadsheet_shows_them() -> None:
    """The header is row 1, so the first data row is row 2 — the number a person sees."""
    raw = (FIXTURES / "import_clean.csv").read_bytes()

    rows = read_rows(raw)

    assert [number for number, _ in rows] == [2, 3, 4]
    assert [row["Business"] for _, row in rows] == [
        "Synthetic Opticians One",
        "Synthetic Agrovet Two",
        "Synthetic Chemist Three",
    ]


def test_a_file_that_is_not_utf8_is_refused() -> None:
    raw = (FIXTURES / "import_not_utf8.csv").read_bytes()

    with pytest.raises(ImportFileError) as error:
        read_rows(raw)

    assert "UTF-8" in str(error.value)


def test_a_header_missing_a_column_we_read_names_the_column() -> None:
    raw = (FIXTURES / "import_missing_column.csv").read_bytes()

    with pytest.raises(ImportFileError) as error:
        read_rows(raw)

    assert "Source" in str(error.value)


def test_an_empty_upload_has_no_header_row() -> None:
    with pytest.raises(ImportFileError):
        read_rows(b"")
