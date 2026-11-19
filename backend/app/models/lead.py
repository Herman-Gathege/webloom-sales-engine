"""The Lead model, extended by the Sprint 2 compliance foundation."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base


class LeadStatus(str, enum.Enum):
    """Scope spec §5.1: the funnel stages, then the ways a lead ends."""

    NEW = "new"
    CONTACTED = "contacted"
    REPLIED = "replied"
    QUALIFIED = "qualified"
    HANDED_OFF = "handed_off"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"
    NO_RESPONSE = "no_response"
    NOT_INTERESTED = "not_interested"
    OPTED_OUT = "opted_out"


class WebsitePresence(str, enum.Enum):
    HAS_WEBSITE = "has_website"
    NO_WEBSITE = "no_website"
    UNKNOWN = "unknown"


NO_WEBSITE_RESEARCH_MARKERS = (
    "no website",
    "new listing",
    "facebook page only",
    "instagram only",
)


def classify_website_presence(
    website_status: str | None,
    has_website: bool,
) -> WebsitePresence:
    """Normalize research into a truthful, campaign-safe website state."""
    if has_website:
        return WebsitePresence.HAS_WEBSITE
    value = (website_status or "").strip().lower()
    if any(marker in value for marker in NO_WEBSITE_RESEARCH_MARKERS):
        return WebsitePresence.NO_WEBSITE
    return WebsitePresence.UNKNOWN


# A varchar plus a check constraint rather than a native Postgres enum: adding a
# status in a later block is then an ordinary migration, not an ALTER TYPE dance.
lead_status_type = Enum(
    LeadStatus,
    name="lead_status",
    native_enum=False,
    length=32,
    validate_strings=True,
    create_constraint=True,
    values_callable=lambda statuses: [status.value for status in statuses],
)


class Lead(Base):
    """A business we might sell to."""

    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(255))
    area: Mapped[str | None] = mapped_column(String(255))
    # E.164, e.g. "+254709709000", and the de-duplication key for imports. NULL
    # until a lead has a phone; Postgres allows many NULLs under one unique
    # constraint, so phone-less leads do not collide with each other.
    phone: Mapped[str | None] = mapped_column(String(32), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    whatsapp_capable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    # Kept verbatim from the research; not normalised in Sprint 1.
    website_status: Mapped[str | None] = mapped_column(Text)
    has_website: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    website_presence: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown", server_default="unknown"
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        lead_status_type,
        nullable=False,
        default=LeadStatus.NEW,
        server_default=LeadStatus.NEW.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    activity: Mapped[list["Activity"]] = relationship(  # noqa: F821
        back_populates="lead",
        order_by="Activity.created_at, Activity.id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    provenance: Mapped["LeadProvenance | None"] = relationship(  # noqa: F821
        back_populates="lead",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    eligibility: Mapped[list["LeadChannelEligibility"]] = relationship(  # noqa: F821
        back_populates="lead",
        order_by="LeadChannelEligibility.channel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    compliance: Mapped["LeadComplianceEvaluation | None"] = relationship(  # noqa: F821
        back_populates="lead",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    suppressions: Mapped[list["Suppression"]] = relationship(  # noqa: F821
        back_populates="lead",
        order_by="Suppression.created_at, Suppression.id",
        passive_deletes=True,
    )

    @property
    def matching_suppressions(self) -> list["Suppression"]:  # noqa: F821
        """All terminal restrictions for the contacts on this lead.

        The repository loads fingerprint matches, including restrictions recorded
        before this lead row was re-imported. The linked relationship is only a
        navigation aid; the fingerprint is what enforcement trusts.
        """
        return getattr(self, "_matching_suppressions", self.suppressions)

    __table_args__ = (
        CheckConstraint("business_name <> ''", name="business_name_not_blank"),
        CheckConstraint("source <> ''", name="source_not_blank"),
        CheckConstraint(
            "website_presence IN ('has_website', 'no_website', 'unknown')",
            name="website_presence_valid",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Lead {self.id} {self.business_name!r}>"
