"""Sprint 5 campaign preparation and immutable outreach drafts."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.models.catalog import MessageTemplate, Offer


class CampaignLeadOutcome(str, enum.Enum):
    PENDING = "pending"
    DRAFTED = "drafted"
    SKIPPED = "skipped"


class OutreachState(str, enum.Enum):
    DRAFT = "draft"


class Campaign(Base):
    """One explicit, prepared batch of leads for one offer and template."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    offer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("message_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    archived_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    offer_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    template_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    selection_context: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    offer: Mapped[Offer] = relationship()
    template: Mapped[MessageTemplate] = relationship()
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])  # noqa: F821
    archived_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[archived_by_id]
    )
    selected_leads: Mapped[list["CampaignLead"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CampaignLead.created_at, CampaignLead.id",
    )
    outreaches: Mapped[list["Outreach"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Outreach.generated_at, Outreach.id",
    )
    events: Mapped[list["CampaignEvent"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CampaignEvent.created_at, CampaignEvent.id",
    )

    __table_args__ = (
        CheckConstraint("name <> ''", name="campaign_name_not_blank"),
        CheckConstraint("goal <> ''", name="campaign_goal_not_blank"),
        CheckConstraint("channel IN ('email', 'sms')", name="campaign_channel_valid"),
        CheckConstraint(
            "selected_count >= 1 AND selected_count <= 200",
            name="campaign_selected_count_valid",
        ),
        CheckConstraint(
            "length(input_fingerprint) = 64",
            name="campaign_input_fingerprint_length",
        ),
        Index("ix_campaigns_archive_generated", "archived_at", "generated_at"),
    )


class CampaignLead(Base):
    """One explicitly selected lead and its final generation outcome."""

    __tablename__ = "campaign_leads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    outcome: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", server_default="pending"
    )
    skip_code: Mapped[str | None] = mapped_column(String(64))
    skip_label: Mapped[str | None] = mapped_column(String(120))
    skip_explanation: Mapped[str | None] = mapped_column(Text)
    eligibility_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    campaign: Mapped[Campaign] = relationship(back_populates="selected_leads")
    lead: Mapped["Lead"] = relationship()  # noqa: F821
    outreach: Mapped["Outreach | None"] = relationship(  # noqa: F821
        back_populates="campaign_lead",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_lead"),
        CheckConstraint(
            "outcome IN ('pending', 'drafted', 'skipped')",
            name="campaign_lead_outcome_valid",
        ),
    )


class Outreach(Base):
    """An immutable generated draft. Sprint 5 never approves or sends it."""

    __tablename__ = "outreaches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaign_leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"), nullable=False
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("message_templates.id", ondelete="RESTRICT"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft", server_default="draft"
    )
    rendered_body: Mapped[str] = mapped_column(Text, nullable=False)
    offer_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    template_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    eligibility_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    sms_encoding: Mapped[str | None] = mapped_column(String(16))
    sms_characters: Mapped[int | None] = mapped_column(Integer)
    sms_units: Mapped[int | None] = mapped_column(Integer)
    sms_segments: Mapped[int | None] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    campaign: Mapped[Campaign] = relationship(back_populates="outreaches")
    campaign_lead: Mapped[CampaignLead] = relationship(back_populates="outreach")
    lead: Mapped["Lead"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "lead_id", "channel", name="uq_outreach_campaign_lead_channel"
        ),
        CheckConstraint("channel IN ('email', 'sms')", name="outreach_channel_valid"),
        CheckConstraint("state = 'draft'", name="outreach_sprint5_state"),
        CheckConstraint("rendered_body <> ''", name="outreach_body_not_blank"),
        CheckConstraint(
            "sms_segments IS NULL OR sms_segments >= 1",
            name="outreach_sms_segments_valid",
        ),
    )


class CampaignEvent(Base):
    """Append-only campaign lifecycle history."""

    __tablename__ = "campaign_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    campaign: Mapped[Campaign] = relationship(back_populates="events")
    actor: Mapped["User | None"] = relationship()  # noqa: F821

    __table_args__ = (
        CheckConstraint("event_type <> ''", name="campaign_event_type_not_blank"),
    )
