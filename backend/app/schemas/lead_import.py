"""Response models for the CSV import endpoint.

The wire shape a screen should call is written out for Herman in
`docs/delivery/sprint-2-import-contract.md`; this file is the code's copy of it.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RefusedRowRead(BaseModel):
    """One row the importer would not create, and the reason a person reads."""

    model_config = ConfigDict(from_attributes=True)

    row: int
    business_name: str
    code: str
    reason: str


class RowWarningRead(BaseModel):
    """One value the importer kept but could not classify."""

    model_config = ConfigDict(from_attributes=True)

    row: int
    field: str
    value: str
    code: str
    message: str


class ImportReviewRowRead(BaseModel):
    """A saved lead whose automated compliance outcome needs attention."""

    model_config = ConfigDict(from_attributes=True)

    row: int
    business_name: str
    compliance_status: Literal["needs_review", "blocked", "invalid"]
    reason_codes: list[str]
    explanation: str


class ImportSummary(BaseModel):
    """POST /api/v1/leads/import — what happened to the upload, row by row.

    `accepted + rejected == row_count` always: every row in the file is either a
    lead or a refusal with a reason. A warning never reduces `accepted`.
    """

    filename: str
    batch_id: UUID
    row_count: int
    accepted: int
    created: int
    rejected: int
    matched: int
    duplicates: int
    eligible: int
    needs_review: int
    blocked: int
    invalid: int
    provenance_incomplete: int
    requiring_review: int
    rejected_rows: list[RefusedRowRead]
    review_rows: list[ImportReviewRowRead]
    warnings: list[RowWarningRead]
