"""The Lead model — the Epic 1 shape in docs/delivery/epic-1-lead-contract.md."""

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
    whatsapp_capable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    # Kept verbatim from the research; not normalised in Epic 1.
    website_status: Mapped[str | None] = mapped_column(Text)
    has_website: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
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

    __table_args__ = (
        CheckConstraint("business_name <> ''", name="business_name_not_blank"),
        CheckConstraint("source <> ''", name="source_not_blank"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Lead {self.id} {self.business_name!r}>"
