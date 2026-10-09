"""Activity — the append-only history shown on the Lead Detail screen."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.models.lead import Lead


class Activity(Base):
    """One thing that happened to one lead. Nothing in Epic 1 edits or deletes it."""

    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    # A stable machine name, e.g. "lead.created"; the UI only picks an icon with it.
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    # "system" until the login block; becomes a real user id later.
    actor: Mapped[str] = mapped_column(
        String(64), nullable=False, default="system", server_default="system"
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lead: Mapped[Lead] = relationship(back_populates="activity")

    __table_args__ = (
        # The detail screen reads one lead's timeline, oldest first.
        Index("ix_activities_lead_id_created_at", "lead_id", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Activity {self.id} {self.type!r} lead={self.lead_id}>"
