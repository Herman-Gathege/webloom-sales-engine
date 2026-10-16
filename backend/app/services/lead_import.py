"""The CSV importer: read the researched list, keep the good rows, explain the rest.

The rules live here. The route reads the upload and delegates; the repository is
the only thing that talks to the database.

Every rule below comes from the real list, not from imagination: the two phone
shapes (`0NNN NNNNNN` mobile, `020 NNNNNNN` Nairobi landline), the landline split
the `WhatsApp capable` column already marks `Call only`, and the handful of ways
`Website status` is written. The shape a screen calls is in
`docs/delivery/sprint-2-import-contract.md`.
"""

import csv
import io
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.models import Activity, Lead, LeadStatus
from app.repositories import LeadRepository

# Bigger than this is refused rather than read into memory. The real list is
# 30 KB; the cap is for whoever uploads a database dump by mistake.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# The columns the importer reads, under the exact headers the research list uses.
# The other columns are either empty in every row (the last seven) or
# deliberately not stored yet — `Date added` and `Opening message` have no column
# in the Sprint 1 Lead shape, so they are raised in the pull request instead of
# being guessed at here.
COLUMNS_READ = (
    "Business",
    "Sector",
    "Area",
    "Phone",
    "WhatsApp capable",
    "Website status",
    "Source",
)

# The words a person reads, kept in one place so Anne's rejected-row wording can
# replace them without touching any logic.
REFUSAL_REASONS: dict[str, str] = {
    "blank_business_name": "The business name is empty.",
    "missing_phone": "No phone number, so this lead cannot be contacted.",
    "unparseable_phone": (
        "The phone number is not in a format we can read"
        " (expected 0NNN NNNNNN or 020 NNNNNNN)."
    ),
    "blank_source": "No source recorded, so we cannot say where this lead came from.",
}
DUPLICATE_PHONE_CODE = "duplicate_phone"
DUPLICATE_IN_FILE_REASON = "This phone number is already on row {row} of the file."
DUPLICATE_IN_SYSTEM_REASON = "This phone number is already in the system."

WARNING_MESSAGES: dict[str, str] = {
    "whatsapp_value_unrecognised": (
        "Not a value we recognise, so it was taken from the phone number instead."
    ),
    "landline_marked_whatsapp": (
        "A landline cannot receive WhatsApp, so it is marked not WhatsApp-capable."
    ),
    "website_status_unclassified": "Website status kept as written; has_website left false.",
    "source_unrecognised": "Source not recognised; stored as a lowercase slug of the value.",
}

# The list's two values. Anything else is reported and worked out from the number
# instead, rather than being read as a yes or a no nobody wrote.
WHATSAPP_VALUES = {"yes": True, "call only": False}

# `Source` is a plain string and the contract's examples are machine values, so
# the display value the list uses is mapped to the one everything else uses. An
# unknown source is slugified and reported, never dropped.
SOURCE_ALIASES = {"google maps listing": "google_maps"}

# Kenyan fixed lines after the country code: 020 Nairobi, 041 Mombasa, and so on.
# Mobiles are 7... and 1..., so the first digit after +254 tells the two apart.
LANDLINE_FIRST_DIGITS = "23456"

NO_WEBSITE_MARKERS = ("no website", "new listing", "facebook page only", "instagram only")
HAS_WEBSITE_MARKERS = ("has a website", "http://", "https://", "www.")

# The same activity the seed writes, so an imported lead's timeline matches a
# seeded one instead of looking like a different kind of lead.
IMPORT_ACTIVITY_SUMMARY = "Imported from the Google Maps list"
RESEARCH_ACTIVITY_SUMMARY = "Website research recorded: {website_status}"
NO_RESEARCH_SUMMARY = "nothing listed"


class ImportFileError(Exception):
    """The upload itself is unusable: not UTF-8, or missing a column we read."""

    def __init__(self, message: str, *, missing_columns: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.message = message
        self.missing_columns = tuple(missing_columns)


@dataclass(frozen=True)
class RefusedRow:
    """One row that will not become a lead, and why."""

    row: int
    business_name: str
    code: str
    reason: str


@dataclass(frozen=True)
class RowWarning:
    """One value that was kept but not understood. Never a refusal."""

    row: int
    field: str
    value: str
    code: str
    message: str


@dataclass(frozen=True)
class ImportResult:
    """What the import did, ready to be shaped into the response."""

    filename: str
    row_count: int
    accepted: int
    rejected: int
    refused: list[RefusedRow]
    warnings: list[RowWarning]


@dataclass(frozen=True)
class _MappedRow:
    """The Lead fields for one row that passed validation."""

    line: int
    business_name: str
    sector: str | None
    area: str | None
    phone: str
    whatsapp_capable: bool
    website_status: str | None
    has_website: bool
    source: str


def read_rows(raw: bytes) -> list[tuple[int, dict[str, str]]]:
    """The file as (row number, row) pairs, header excluded. Raises ImportFileError.

    The row number counts records with the header as row 1, which is the number
    the person sees in Excel beside the row they have to fix.
    """
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportFileError(
            "The file is not UTF-8 text. Save the list as a UTF-8 CSV and try again."
        ) from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ImportFileError("The file has no header row.")

    missing = [column for column in COLUMNS_READ if column not in reader.fieldnames]
    if missing:
        raise ImportFileError(
            "The file is missing these columns: " + ", ".join(missing) + ".",
            missing_columns=missing,
        )

    rows: list[tuple[int, dict[str, str]]] = []
    for line, row in enumerate(reader, start=2):
        # A row with more fields than the header arrives under a None key.
        rows.append((line, {key: (value or "") for key, value in row.items() if key}))
    return rows


def normalise_phone(raw: str) -> str:
    """E.164 for the list's two shapes, or ValueError.

    `0NNN NNNNNN` is a mobile and `020 NNNNNNN` a Nairobi landline; both become
    `+254…`. This is the de-duplication key, so an unrecognised shape is a
    refusal rather than a guess.
    """
    compact = re.sub(r"[\s\-().]", "", raw.strip())
    if compact.startswith("+"):
        digits = compact[1:]
        # 254 plus the nine digits that follow it — nothing longer, nothing shorter.
        if digits.isdigit() and len(digits) == 12 and digits.startswith("254"):
            return f"+{digits}"
        raise ValueError(raw)
    if compact.isdigit() and len(compact) == 10 and compact.startswith("0"):
        return f"+254{compact[1:]}"
    raise ValueError(raw)


def parse_website_status(raw: str) -> tuple[bool, bool]:
    """(has_website, understood) for one raw `Website status` string.

    The list says the same handful of things — `3,713 reviews - no website
    listed`, `New listing - no website`, `23 reviews - Facebook page only`. The
    raw string is stored verbatim either way, so a value we do not recognise is
    reported rather than guessed at, and nothing is lost. An empty cell is
    reported too: it means no research was recorded.
    """
    value = raw.strip().lower()
    if any(marker in value for marker in NO_WEBSITE_MARKERS):
        return False, True
    if any(marker in value for marker in HAS_WEBSITE_MARKERS):
        return True, True
    return False, False


def normalise_source(raw: str) -> tuple[str, bool]:
    """(source, understood). `Google Maps listing` becomes `google_maps`."""
    value = " ".join(raw.split())
    if not value:
        return "", False
    known = SOURCE_ALIASES.get(value.lower())
    if known is not None:
        return known, True
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_"), False


def is_landline(phone: str) -> bool:
    return len(phone) > 4 and phone.startswith("+254") and phone[4] in LANDLINE_FIRST_DIGITS


def refusal_for(line: int, row: dict[str, str]) -> RefusedRow | None:
    """The one reason this row cannot be imported, or None.

    Checked in a fixed order — business name, phone, source — so a row with
    several problems always reports the same one.
    """
    business_name = row["Business"].strip()
    if not business_name:
        return RefusedRow(line, "", "blank_business_name", REFUSAL_REASONS["blank_business_name"])

    phone = row["Phone"].strip()
    if not phone:
        return RefusedRow(line, business_name, "missing_phone", REFUSAL_REASONS["missing_phone"])
    try:
        normalise_phone(phone)
    except ValueError:
        return RefusedRow(
            line, business_name, "unparseable_phone", REFUSAL_REASONS["unparseable_phone"]
        )

    if not normalise_source(row["Source"])[0]:
        # Empty, or nothing but punctuation: either way there is no source to record.
        return RefusedRow(line, business_name, "blank_source", REFUSAL_REASONS["blank_source"])
    return None


def map_row(line: int, row: dict[str, str]) -> tuple[_MappedRow, list[RowWarning]]:
    """The Lead fields for a row that passed `refusal_for`, plus its warnings.

    A warning never refuses a row: the value is kept as it was written, and a
    person is told which value we could not classify.
    """
    warnings: list[RowWarning] = []

    def warn(field: str, value: str, code: str) -> None:
        warnings.append(RowWarning(line, field, value, code, WARNING_MESSAGES[code]))

    business_name = row["Business"].strip()
    phone = normalise_phone(row["Phone"].strip())
    landline = is_landline(phone)

    # `sector` is free text in the contract and the controlled vocabulary is a
    # later sprint's decision, so it is stored exactly as written: with no
    # vocabulary to check a value against there is no such thing as an unmapped
    # sector, and nothing to report about one.
    sector = row["Sector"].strip() or None

    whatsapp_raw = row["WhatsApp capable"].strip()
    whatsapp_capable = WHATSAPP_VALUES.get(whatsapp_raw.lower())
    if whatsapp_capable is None:
        # All six of the list's landlines already say `Call only`; when the column
        # says something we do not know, the number's own shape decides.
        warn("whatsapp_capable", whatsapp_raw, "whatsapp_value_unrecognised")
        whatsapp_capable = not landline
    if landline and whatsapp_capable:
        # The contract is explicit — `whatsapp_capable` is false for landlines —
        # so the number wins over the column, and the contradiction is reported.
        warn("whatsapp_capable", whatsapp_raw, "landline_marked_whatsapp")
        whatsapp_capable = False

    website_status = row["Website status"].strip()
    has_website, understood = parse_website_status(website_status)
    if not understood:
        warn("website_status", website_status, "website_status_unclassified")

    source_raw = row["Source"].strip()
    source, source_understood = normalise_source(source_raw)
    if not source_understood:
        warn("source", source_raw, "source_unrecognised")

    mapped = _MappedRow(
        line=line,
        business_name=business_name,
        # Both are free text in the contract, so they are stored as written; any
        # controlled vocabulary is a later sprint's decision, not a guess here.
        sector=sector,
        area=row["Area"].strip() or None,
        phone=phone,
        whatsapp_capable=whatsapp_capable,
        website_status=website_status or None,
        has_website=has_website,
        source=source,
    )
    return mapped, warnings


def refused_rows_csv(result: ImportResult) -> str:
    """The downloadable error report: one line per refused row."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["row", "business_name", "code", "reason"])
    for refused in result.refused:
        writer.writerow([refused.row, refused.business_name, refused.code, refused.reason])
    return buffer.getvalue()


class LeadImportService:
    """Turns an uploaded research CSV into leads, and explains every refusal."""

    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def import_file(self, raw: bytes, filename: str) -> ImportResult:
        """Import every good row and refuse the rest. Raises ImportFileError."""
        rows = read_rows(raw)
        imported_at = datetime.now(UTC)

        refused: list[RefusedRow] = []
        warnings: list[RowWarning] = []
        candidates: list[_MappedRow] = []
        seen_in_file: dict[str, int] = {}

        for line, row in rows:
            refusal = refusal_for(line, row)
            if refusal is not None:
                refused.append(refusal)
                continue

            mapped, row_warnings = map_row(line, row)
            warnings.extend(row_warnings)

            earlier_line = seen_in_file.get(mapped.phone)
            if earlier_line is not None:
                refused.append(
                    RefusedRow(
                        mapped.line,
                        mapped.business_name,
                        DUPLICATE_PHONE_CODE,
                        DUPLICATE_IN_FILE_REASON.format(row=earlier_line),
                    )
                )
                continue

            seen_in_file[mapped.phone] = line
            candidates.append(mapped)

        accepted = self._drop_known_phones(candidates, refused)
        self._save(accepted, imported_at)
        refused.sort(key=lambda row: row.row)

        return ImportResult(
            filename=filename,
            row_count=len(rows),
            accepted=len(accepted),
            rejected=len(refused),
            refused=refused,
            warnings=warnings,
        )

    def _drop_known_phones(
        self, candidates: list[_MappedRow], refused: list[RefusedRow]
    ) -> list[_MappedRow]:
        """Keep the numbers we do not already hold, refusing the ones we do."""
        already_held = self.repository.existing_phones([row.phone for row in candidates])
        accepted: list[_MappedRow] = []
        for mapped in candidates:
            if mapped.phone in already_held:
                refused.append(
                    RefusedRow(
                        mapped.line,
                        mapped.business_name,
                        DUPLICATE_PHONE_CODE,
                        DUPLICATE_IN_SYSTEM_REASON,
                    )
                )
                continue
            accepted.append(mapped)
        return accepted

    def _save(self, accepted: Sequence[_MappedRow], imported_at: datetime) -> None:
        """Write every accepted lead in one transaction.

        The accepted rows are one second apart, the file's first row newest, so
        the Lead List reads in the file's own order and importing the same list
        twice produces the same order. The whole file commits once, so a rejected
        row cannot take a good one down with it.
        """
        for index, mapped in enumerate(accepted):
            created_at = imported_at - timedelta(seconds=index)
            lead = Lead(
                business_name=mapped.business_name,
                sector=mapped.sector,
                area=mapped.area,
                phone=mapped.phone,
                whatsapp_capable=mapped.whatsapp_capable,
                website_status=mapped.website_status,
                has_website=mapped.has_website,
                source=mapped.source,
                status=LeadStatus.NEW,
                created_at=created_at,
                updated_at=created_at,
            )
            lead.activity.append(
                Activity(
                    type="lead.created",
                    actor="system",
                    summary=IMPORT_ACTIVITY_SUMMARY,
                    created_at=created_at,
                )
            )
            # Always two entries, like a seeded lead, so an imported lead's
            # timeline is not a different shape from a seeded one.
            lead.activity.append(
                Activity(
                    type="lead.researched",
                    actor="system",
                    summary=RESEARCH_ACTIVITY_SUMMARY.format(
                        website_status=mapped.website_status or NO_RESEARCH_SUMMARY
                    ),
                    # Half a minute later, so the timeline has one order rather
                    # than two rows sharing a timestamp.
                    created_at=created_at + timedelta(seconds=30),
                )
            )
            self.repository.add(lead)

        self.repository.commit()
