"""The idempotent seed. Running it twice must not create a second copy."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Lead
from app.repositories import LeadRepository
from app.seed.sample_data import build_sample_leads


@dataclass(frozen=True)
class SeedResult:
    leads_created: int
    leads_skipped: int
    activity_created: int

    def describe(self) -> str:
        return (
            f"{self.leads_created} leads created, {self.leads_skipped} already present, "
            f"{self.activity_created} activity entries created"
        )


def seed_sample_leads(session: Session, *, leads: list[Lead] | None = None) -> SeedResult:
    """Insert the synthetic sample leads that are not in the database yet.

    Repeatable in two independent ways: each lead has a fixed id, and phone is
    the de-duplication key the contract names. A lead that matches either is
    left exactly as it is — the seed never updates or deletes a row.
    """
    repository = LeadRepository(session)
    candidates = build_sample_leads() if leads is None else leads

    created = 0
    skipped = 0
    activity_created = 0

    for candidate in candidates:
        if repository.get(candidate.id) is not None:
            skipped += 1
            continue
        if candidate.phone is not None and repository.find_by_phone(candidate.phone) is not None:
            skipped += 1
            continue

        session.add(candidate)
        created += 1
        activity_created += len(candidate.activity)

    session.commit()
    return SeedResult(
        leads_created=created, leads_skipped=skipped, activity_created=activity_created
    )
