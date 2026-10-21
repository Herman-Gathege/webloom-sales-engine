"""Response models for Lead. These are the JSON shapes in the contract.

Field names are snake_case and identical to the database columns, so nothing
here is a mapping layer: the contract, the columns, and the JSON all agree.
"""

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.lead import LeadStatus
from app.schemas.activity import ActivityRead
from app.schemas.types import UtcDatetime


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_name: str
    sector: str | None
    area: str | None
    phone: str | None
    email: str | None
    whatsapp_capable: bool
    website_status: str | None
    has_website: bool
    source: str
    status: LeadStatus
    created_at: UtcDatetime
    updated_at: UtcDatetime


class LeadProvenanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    import_batch_id: uuid.UUID | None
    row_number: int | None
    source_url: str | None
    collection_date: date | None
    collection_method: str | None
    intended_purpose: str | None
    contact_type: Literal["unknown", "generic_business", "named_individual"]
    contact_name: str | None


class ChannelEligibilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel: Literal["email", "sms", "whatsapp"]
    state: Literal["needs_review", "eligible"]
    effective_state: Literal["needs_review", "eligible", "suppressed"]
    lawful_basis: str | None
    evidence_summary: str | None
    evidence_source: str | None
    intended_purpose: str | None
    contact_context: str | None
    reviewer: str | None
    reviewed_at: UtcDatetime | None
    rationale: str | None


class SuppressionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contact_kind: Literal["phone", "email"]
    scope: Literal["all_marketing", "email", "sms", "whatsapp"]
    reason: Literal["opt_out", "objection", "manual_restriction"]
    source: str
    recorded_by: str
    note: str | None
    created_at: UtcDatetime


class LeadDetailRead(LeadRead):
    """GET /api/v1/leads/{id} — every Lead field, plus its history.

    `activity` is oldest first and `[]` when nothing has happened yet, never null.
    """

    provenance: LeadProvenanceRead | None
    eligibility: list[ChannelEligibilityRead]
    suppressions: list[SuppressionRead]
    activity: list[ActivityRead]


class LeadListRead(BaseModel):
    """GET /api/v1/leads — one page, plus the total before pagination."""

    items: list[LeadRead]
    total: int
    limit: int
    offset: int


class EligibilityReviewRequest(BaseModel):
    """One human review decision for one channel."""

    state: Literal["needs_review", "eligible"]
    lawful_basis: Literal[
        "consent",
        "contract",
        "legal_obligation",
        "vital_interests",
        "public_task",
        "legitimate_interests",
        "other",
    ] | None = None
    evidence_summary: str | None = Field(default=None, max_length=4000)
    evidence_source: str | None = Field(default=None, max_length=2000)
    intended_purpose: str | None = Field(default=None, max_length=2000)
    contact_context: str | None = Field(default=None, max_length=2000)
    reviewer: str = Field(min_length=1, max_length=64)
    rationale: str = Field(min_length=1, max_length=4000)

    @field_validator("reviewer", "rationale")
    @classmethod
    def review_text_is_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def eligible_decisions_carry_evidence(self) -> "EligibilityReviewRequest":
        if self.state != "eligible":
            return self
        missing = [
            name
            for name in (
                "lawful_basis",
                "evidence_summary",
                "evidence_source",
                "intended_purpose",
                "contact_context",
            )
            if not getattr(self, name) or not str(getattr(self, name)).strip()
        ]
        if missing:
            raise ValueError("Eligible reviews require: " + ", ".join(missing))
        return self


class SuppressionCreate(BaseModel):
    """Record an opt-out or restriction; there is intentionally no delete shape."""

    scope: Literal["all_marketing", "email", "sms", "whatsapp"]
    reason: Literal["opt_out", "objection", "manual_restriction"]
    source: str = Field(min_length=1, max_length=255)
    recorded_by: str = Field(min_length=1, max_length=64)
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("source", "recorded_by")
    @classmethod
    def suppression_text_is_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
