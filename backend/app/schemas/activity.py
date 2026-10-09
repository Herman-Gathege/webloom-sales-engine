"""Response models for Activity. These are the JSON shapes in the contract."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.types import UtcDatetime


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lead_id: uuid.UUID
    type: str
    actor: str
    summary: str
    created_at: UtcDatetime
