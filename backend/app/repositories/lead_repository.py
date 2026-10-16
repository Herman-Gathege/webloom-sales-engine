"""Data access for leads. The only place that writes queries for them."""

import uuid
from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Activity, Lead


class LeadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_leads(self, *, limit: int, offset: int) -> tuple[list[Lead], int]:
        """One page of leads, newest first, plus the count before pagination.

        The id tie-breaker keeps the order stable when two rows share a
        created_at, so a page boundary cannot repeat or skip a lead.
        """
        total = self.session.scalar(select(func.count()).select_from(Lead)) or 0
        statement = (
            select(Lead)
            .order_by(Lead.created_at.desc(), Lead.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all()), total

    def get(self, lead_id: uuid.UUID) -> Lead | None:
        return self.session.get(Lead, lead_id)

    def get_with_activity(self, lead_id: uuid.UUID) -> Lead | None:
        """The lead and its history in two queries rather than one per row."""
        statement = select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.activity))
        return self.session.scalar(statement)

    def find_by_phone(self, phone: str) -> Lead | None:
        return self.session.scalar(select(Lead).where(Lead.phone == phone))

    def existing_phones(self, phones: Iterable[str]) -> set[str]:
        """Which of these numbers we already hold, in one query.

        The importer asks once for a whole file rather than once per row: 52
        row-by-row lookups would be 52 round trips for an answer one query gives.
        """
        wanted = list(phones)
        if not wanted:
            return set()
        rows = self.session.scalars(select(Lead.phone).where(Lead.phone.in_(wanted)))
        return {phone for phone in rows if phone is not None}

    def add(self, lead: Lead) -> Lead:
        self.session.add(lead)
        return lead

    def add_activity(self, activity: Activity) -> Activity:
        self.session.add(activity)
        return activity

    def count_activity(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Activity)) or 0

    def commit(self) -> None:
        """Save the unit of work — the importer writes all its accepted rows at once."""
        self.session.commit()
