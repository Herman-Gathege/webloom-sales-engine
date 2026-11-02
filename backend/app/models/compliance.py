"""Compliance records for provenance, channel review, and terminal suppression."""

import re
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
from app.models.lead import Lead


class ImportBatch(Base):
    """One imported CSV, including batches where every row was refused."""

    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    matched: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    eligible: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    needs_review: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    blocked: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    invalid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    provenance_incomplete: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    review_required: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    imported_by: Mapped[str] = mapped_column(
        String(64), nullable=False, default="system", server_default="system"
    )

    provenance: Mapped[list["LeadProvenance"]] = relationship(back_populates="import_batch")

    __table_args__ = (
        CheckConstraint("filename <> ''", name="filename_not_blank"),
        CheckConstraint("row_count >= 0", name="row_count_non_negative"),
        CheckConstraint("accepted >= 0", name="accepted_non_negative"),
        CheckConstraint("rejected >= 0", name="rejected_non_negative"),
        CheckConstraint("duplicates >= 0", name="duplicates_non_negative"),
        CheckConstraint("matched >= 0", name="matched_non_negative"),
        CheckConstraint("eligible >= 0", name="eligible_non_negative"),
        CheckConstraint("needs_review >= 0", name="needs_review_non_negative"),
        CheckConstraint("blocked >= 0", name="blocked_non_negative"),
        CheckConstraint("invalid >= 0", name="invalid_non_negative"),
        CheckConstraint(
            "provenance_incomplete >= 0",
            name="provenance_incomplete_non_negative",
        ),
        CheckConstraint("review_required >= 0", name="review_required_non_negative"),
    )


class LeadProvenance(Base):
    """Where one lead came from and why we intended to process it."""

    __tablename__ = "lead_provenance"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="SET NULL")
    )
    row_number: Mapped[int | None] = mapped_column(Integer)
    source_name: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    collection_date: Mapped[date | None] = mapped_column(Date)
    collection_method: Mapped[str | None] = mapped_column(String(255))
    intended_purpose: Mapped[str | None] = mapped_column(Text)
    contact_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown", server_default="unknown"
    )
    contact_name: Mapped[str | None] = mapped_column(String(255))

    lead: Mapped[Lead] = relationship(back_populates="provenance")
    import_batch: Mapped[ImportBatch | None] = relationship(back_populates="provenance")

    __table_args__ = (
        CheckConstraint(
            "contact_type IN ('unknown', 'generic_business', 'named_individual')",
            name="contact_type_valid",
        ),
        CheckConstraint("row_number IS NULL OR row_number >= 2", name="row_number_valid"),
    )


class LeadChannelEligibility(Base):
    """The persisted human review for one lead and one channel."""

    __tablename__ = "lead_channel_eligibility"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="needs_review", server_default="needs_review"
    )
    lawful_basis: Mapped[str | None] = mapped_column(String(32))
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    evidence_source: Mapped[str | None] = mapped_column(Text)
    intended_purpose: Mapped[str | None] = mapped_column(Text)
    contact_context: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str | None] = mapped_column(String(64))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rationale: Mapped[str | None] = mapped_column(Text)
    reviewed_input_fingerprint: Mapped[str | None] = mapped_column(String(64))

    lead: Mapped[Lead] = relationship(back_populates="eligibility")

    @property
    def effective_state(self) -> str:
        """Suppression always wins over a previous human review."""
        suppressed_scopes = {
            suppression.scope for suppression in self.lead.matching_suppressions
        }
        if "all_marketing" in suppressed_scopes or self.channel in suppressed_scopes:
            return "suppressed"
        return self.state

    @property
    def technical_available(self) -> bool:
        """Whether the selected channel can use a contact currently on this lead."""
        if self.channel == "email":
            return bool(
                self.lead.email
                and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.lead.email)
            )

        phone = self.lead.phone
        if not phone or not re.fullmatch(r"\+254\d{9}", phone):
            return False
        if self.channel == "whatsapp":
            return self.lead.whatsapp_capable

        # Kenyan fixed lines cannot receive SMS. A future international format
        # remains technically available until a channel validator defines it.
        kenyan_fixed_line = (
            phone.startswith("+254") and len(phone) > 4 and phone[4] in "23456"
        )
        return not kenyan_fixed_line

    __table_args__ = (
        UniqueConstraint("lead_id", "channel", name="uq_lead_channel_eligibility_lead_channel"),
        CheckConstraint("channel IN ('email', 'sms', 'whatsapp')", name="channel_valid"),
        CheckConstraint(
            "state IN ('needs_review', 'eligible')", name="eligibility_state_valid"
        ),
        CheckConstraint(
            "lawful_basis IS NULL OR lawful_basis IN "
            "('consent', 'contract', 'legal_obligation', 'vital_interests', "
            "'public_interest', 'legitimate_interests', 'research_statistics')",
            name="lawful_basis_valid",
        ),
        CheckConstraint(
            "state <> 'eligible' OR ("
            "lawful_basis IS NOT NULL AND evidence_summary IS NOT NULL AND "
            "evidence_source IS NOT NULL AND intended_purpose IS NOT NULL AND "
            "contact_context IS NOT NULL AND reviewer IS NOT NULL AND "
            "reviewed_at IS NOT NULL AND rationale IS NOT NULL)",
            name="eligible_review_complete",
        ),
    )


class LeadComplianceEvaluation(Base):
    """The latest automatic compliance snapshot for one lead.

    Human evidence remains in `LeadChannelEligibility`. This record stores the
    derived lead-level outcome, its reasons, and the exact rule/input version so
    unchanged decisions can be reused without another human review.
    """

    __tablename__ = "lead_compliance_evaluation"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    data_quality_status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    eligible_channels: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    suppressed_channels: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    channel_results: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    outreach_ready: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    lead: Mapped[Lead] = relationship(back_populates="compliance")

    __table_args__ = (
        CheckConstraint(
            "status IN ('eligible', 'needs_review', 'blocked', 'invalid')",
            name="compliance_status_valid",
        ),
        CheckConstraint(
            "data_quality_status IN ('complete', 'incomplete', 'invalid')",
            name="data_quality_status_valid",
        ),
        CheckConstraint(
            "outreach_ready = (status = 'eligible')",
            name="outreach_ready_matches_eligible",
        ),
        CheckConstraint("explanation <> ''", name="explanation_not_blank"),
        CheckConstraint("rule_version <> ''", name="rule_version_not_blank"),
        CheckConstraint(
            "length(input_fingerprint) = 64", name="input_fingerprint_length"
        ),
    )


class Suppression(Base):
    """A terminal, contact-level marketing restriction independent of any lead row."""

    __tablename__ = "suppressions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # The lead link is for operator navigation only. The fingerprint is canonical,
    # so deleting and later re-importing a lead cannot erase the restriction.
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL")
    )
    contact_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    contact_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    recorded_by: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lead: Mapped[Lead | None] = relationship(back_populates="suppressions")

    __table_args__ = (
        UniqueConstraint("contact_fingerprint", "scope", name="uq_suppression_contact_scope"),
        CheckConstraint("contact_kind IN ('phone', 'email')", name="contact_kind_valid"),
        CheckConstraint(
            "scope IN ('all_marketing', 'email', 'sms', 'whatsapp')", name="scope_valid"
        ),
        CheckConstraint(
            "reason IN ('opt_out', 'objection', 'manual_restriction')", name="reason_valid"
        ),
        CheckConstraint("source <> ''", name="source_not_blank"),
        CheckConstraint("recorded_by <> ''", name="recorded_by_not_blank"),
        Index("ix_suppressions_contact_fingerprint", "contact_fingerprint"),
    )
