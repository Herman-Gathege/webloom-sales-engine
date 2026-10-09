"""Lead business rules. Routes parse and delegate; the rules live here."""

import uuid
from dataclasses import dataclass

from app.models import Lead
from app.repositories import LeadRepository

# The contract caps a page at 200 items, whatever the caller asks for.
MAX_LIMIT = 200
DEFAULT_LIMIT = 50


class LeadNotFoundError(Exception):
    """Raised for an unknown id, and for an id that is not a uuid at all.

    A malformed id is a missing lead, not a server error: the contract says it
    answers 404, so there is no separate InvalidLeadId error to handle.
    """


@dataclass(frozen=True)
class LeadPage:
    items: list[Lead]
    total: int
    limit: int
    offset: int


class LeadService:
    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def list_leads(self, *, limit: int, offset: int) -> LeadPage:
        effective_limit = min(limit, MAX_LIMIT)
        items, total = self.repository.list_leads(limit=effective_limit, offset=offset)
        return LeadPage(items=items, total=total, limit=effective_limit, offset=offset)

    def get_lead(self, lead_id: str) -> Lead:
        """One lead with its activity, oldest first. Raises LeadNotFoundError."""
        lead = self.repository.get_with_activity(self._parse_id(lead_id))
        if lead is None:
            raise LeadNotFoundError(lead_id)
        return lead

    @staticmethod
    def _parse_id(lead_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(lead_id)
        except (ValueError, AttributeError, TypeError) as exc:
            # Not a uuid, so it cannot be a lead we hold.
            raise LeadNotFoundError(lead_id) from exc
