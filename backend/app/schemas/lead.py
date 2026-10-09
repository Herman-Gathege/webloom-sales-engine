"""Response models for Lead. These are the JSON shapes in the contract.

Field names are snake_case and identical to the database columns, so nothing
here is a mapping layer: the contract, the columns, and the JSON all agree.
"""

import uuid

from pydantic import BaseModel, ConfigDict

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
    whatsapp_capable: bool
    website_status: str | None
    has_website: bool
    source: str
    status: LeadStatus
    created_at: UtcDatetime
    updated_at: UtcDatetime


class LeadDetailRead(LeadRead):
    """GET /api/v1/leads/{id} — every Lead field, plus its history.

    `activity` is oldest first and `[]` when nothing has happened yet, never null.
    """

    activity: list[ActivityRead]


class LeadListRead(BaseModel):
    """GET /api/v1/leads — one page, plus the total before pagination."""

    items: list[LeadRead]
    total: int
    limit: int
    offset: int
