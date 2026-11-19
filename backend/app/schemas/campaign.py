"""Sprint 5 campaign, preview and immutable draft contracts."""

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models import TemplateChannel, WebsitePresence
from app.schemas.types import UtcDatetime


class CampaignSelectionContext(BaseModel):
    q: str | None = Field(default=None, max_length=255)
    sector: str | None = Field(default=None, max_length=255)
    area: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=64)
    website: Literal["yes", "no", "unknown"] | None = None
    status: str | None = Field(default=None, max_length=32)
    compliance_status: Literal["eligible", "needs_review", "blocked", "invalid"] | None = None
    data_quality_status: Literal["complete", "incomplete", "invalid"] | None = None
    provenance: Literal["available", "missing", "incomplete"] | None = None
    outreach_ready: bool | None = None
    exception_review: bool | None = None
    has_suppression: bool | None = None
    batch_id: uuid.UUID | None = None


class CampaignInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=2000)
    offer_id: uuid.UUID
    template_id: uuid.UUID
    channel: TemplateChannel = TemplateChannel.SMS
    lead_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)
    selection_context: CampaignSelectionContext = Field(
        default_factory=CampaignSelectionContext
    )

    @field_validator("name", "goal")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = " ".join(value.split())
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("lead_ids")
    @classmethod
    def unique_lead_ids(cls, values: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(values) != len(set(values)):
            raise ValueError("Select each lead only once.")
        return values


class CampaignUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=2000)
    offer_id: uuid.UUID
    template_id: uuid.UUID
    channel: TemplateChannel = TemplateChannel.SMS
    lead_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)
    selection_context: CampaignSelectionContext = Field(
        default_factory=CampaignSelectionContext
    )

    @field_validator("name", "goal")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = " ".join(value.split())
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("lead_ids")
    @classmethod
    def unique_lead_ids(cls, values: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(values) != len(set(values)):
            raise ValueError("Select each lead only once.")
        return values


class CampaignPreviewLeadRead(BaseModel):
    lead_id: uuid.UUID
    business_name: str
    sector: str | None
    area: str | None
    source: str
    website_presence: WebsitePresence
    decision_type: Literal["automated_policy", "human_review", "none"]
    explanation: str
    policy_id: str | None
    policy_version: str | None
    technical_available: bool
    research_date: date | None
    research_stale: bool


class CampaignSkipRead(BaseModel):
    lead_id: uuid.UUID
    business_name: str
    code: str
    label: str
    explanation: str
    reason_codes: list[str]


class CampaignPreviewRead(BaseModel):
    eligible_count: int
    skipped_count: int
    eligible: list[CampaignPreviewLeadRead]
    skipped: list[CampaignSkipRead]
    reason_counts: dict[str, int]


class CampaignSummaryRead(BaseModel):
    id: uuid.UUID
    name: str
    goal: str
    channel: TemplateChannel
    owner_id: uuid.UUID
    owner_email: str
    offer_id: uuid.UUID
    offer_name: str
    template_id: uuid.UUID
    template_name: str
    selected_count: int
    draft_count: int
    skip_count: int
    status: Literal["draft", "generated", "archived"]
    created_at: UtcDatetime
    updated_at: UtcDatetime
    last_activity_at: UtcDatetime
    generated_at: UtcDatetime | None
    archived_at: UtcDatetime | None
    archived_by_email: str | None


class CampaignDraftRead(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    business_name: str
    sector: str | None
    area: str | None
    channel: TemplateChannel
    state: Literal["draft"]
    rendered_body: str
    sms_encoding: str | None
    sms_characters: int | None
    sms_units: int | None
    sms_segments: int | None
    eligibility_snapshot: dict[str, object]
    template_snapshot: dict[str, object]
    offer_snapshot: dict[str, object]
    generated_at: UtcDatetime
    research_date: date | None
    research_stale: bool


class CampaignEventRead(BaseModel):
    event_type: str
    actor_email: str | None
    details: dict[str, object] | None
    created_at: UtcDatetime


class CampaignDetailRead(CampaignSummaryRead):
    offer_snapshot: dict[str, object]
    template_snapshot: dict[str, object]
    input_fingerprint: str
    selection_context: dict[str, object]
    selected_lead_ids: list[uuid.UUID]
    drafts: list[CampaignDraftRead]
    skips: list[CampaignSkipRead]
    events: list[CampaignEventRead]


class CampaignListRead(BaseModel):
    items: list[CampaignSummaryRead]
