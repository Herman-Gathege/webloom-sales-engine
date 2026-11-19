"""Lead business rules. Routes parse and delegate; the rules live here."""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal
from urllib.parse import urlsplit

from sqlalchemy.exc import IntegrityError

from app.models import (
    Activity,
    Lead,
    LeadChannelEligibility,
    LeadProvenance,
    LeadStatus,
)
from app.repositories import LeadRepository
from app.schemas.lead import LeadCreate
from app.services.compliance_evaluator import ComplianceEvaluator
from app.services.contact_identity import normalize_email, valid_email
from app.services.lead_import import (
    NO_RESEARCH_SUMMARY,
    RESEARCH_ACTIVITY_SUMMARY,
    is_landline,
    normalise_phone,
    normalise_source,
    normalise_text,
    parse_website_status,
)

# The contract caps a page at 200 items, whatever the caller asks for.
MAX_LIMIT = 200
DEFAULT_LIMIT = 50


class LeadNotFoundError(Exception):
    """Raised for an unknown id, and for an id that is not a uuid at all.

    A malformed id is a missing lead, not a server error: the contract says it
    answers 404, so there is no separate InvalidLeadId error to handle.
    """


class LeadConflictError(Exception):
    """The supplied phone number already identifies a lead."""


class LeadValidationError(Exception):
    """A manually entered value cannot be stored safely."""

    def __init__(self, message: str, *, field: str) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


@dataclass(frozen=True)
class LeadPage:
    items: list[Lead]
    total: int
    limit: int
    offset: int


class LeadService:
    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def list_leads(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None = None,
        sector: str | None = None,
        area: str | None = None,
        source: str | None = None,
        website: Literal["yes", "no"] | None = None,
        status: str | None = None,
        compliance_status: str | None = None,
        data_quality_status: str | None = None,
        provenance: Literal["available", "missing", "incomplete"] | None = None,
        outreach_ready: bool | None = None,
        exception_review: bool | None = None,
        has_suppression: bool | None = None,
        batch_id: uuid.UUID | None = None,
        sort: Literal[
            "newest", "oldest", "business_name", "compliance_status"
        ] = "newest",
    ) -> LeadPage:
        effective_limit = min(limit, MAX_LIMIT)
        items, total = self.repository.list_leads(
            limit=effective_limit,
            offset=offset,
            q=q,
            sector=sector,
            area=area,
            source=source,
            website=website,
            lead_status=status,
            compliance_status=compliance_status,
            data_quality_status=data_quality_status,
            provenance=provenance,
            outreach_ready=outreach_ready,
            exception_review=exception_review,
            has_suppression=has_suppression,
            batch_id=batch_id,
            sort=sort,
        )
        return LeadPage(items=items, total=total, limit=effective_limit, offset=offset)

    def filter_options(self) -> dict[str, object]:
        return self.repository.filter_options()

    def get_lead(self, lead_id: str) -> Lead:
        """One lead with its activity, oldest first. Raises LeadNotFoundError."""
        lead = self.repository.get_with_activity(self._parse_id(lead_id))
        if lead is None:
            raise LeadNotFoundError(lead_id)
        return lead

    def create_lead(self, values: LeadCreate, *, actor: str) -> Lead:
        """Create one researched lead through the same rules as the importer."""
        business_name = normalise_text(values.business_name)
        if not business_name:
            raise LeadValidationError(
                "Enter the business name.", field="business_name"
            )

        phone: str | None = None
        if values.phone:
            try:
                phone = normalise_phone(values.phone)
            except ValueError as exc:
                raise LeadValidationError(
                    "Enter a phone as 0NNN NNNNNN, 020 NNNNNNN, or +254….",
                    field="phone",
                ) from exc

        email = normalize_email(values.email) if values.email else None
        if email and not valid_email(email):
            raise LeadValidationError(
                "Enter a valid email address or leave it blank.", field="email"
            )
        duplicate = self.repository.find_manual_duplicate(
            business_name=business_name,
            phone=phone,
            email=email,
        )
        if duplicate is not None:
            if phone and duplicate.phone == phone:
                raise LeadConflictError(
                    "A lead with this phone number already exists."
                )
            raise LeadConflictError(
                "A lead for this business and email already exists."
            )

        source_raw = normalise_text(values.source)
        source, _ = normalise_source(source_raw)
        if not source:
            raise LeadValidationError(
                "Say where this lead came from.", field="source"
            )
        if len(source) > 64:
            raise LeadValidationError(
                "The source name is too long. Use a shorter description.",
                field="source",
            )

        source_url = values.source_url
        if source_url:
            parsed_url = urlsplit(source_url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                raise LeadValidationError(
                    "Enter the source as a full http:// or https:// link.",
                    field="source_url",
                )

        website_status = (
            normalise_text(values.website_status) if values.website_status else None
        )
        parsed_has_website, _ = parse_website_status(website_status or "")
        has_website = values.has_website or parsed_has_website
        whatsapp_capable = bool(
            phone and values.whatsapp_capable and not is_landline(phone)
        )
        created_at = datetime.now(UTC)

        lead = Lead(
            business_name=business_name,
            sector=normalise_text(values.sector) if values.sector else None,
            area=normalise_text(values.area) if values.area else None,
            phone=phone,
            email=email,
            whatsapp_capable=whatsapp_capable,
            website_status=website_status,
            has_website=has_website,
            source=source,
            status=LeadStatus.NEW,
            created_at=created_at,
            updated_at=created_at,
        )
        lead.provenance = LeadProvenance(
            source_name=normalise_text(values.source_name or source_raw),
            source_url=source_url,
            collection_date=values.collection_date or date.today(),
            collection_method=(
                normalise_text(values.collection_method)
                if values.collection_method
                else "Manual seller entry"
            ),
            intended_purpose=(
                normalise_text(values.intended_purpose)
                if values.intended_purpose
                else "Business outreach"
            ),
            contact_type=values.contact_type,
            contact_name=(
                normalise_text(values.contact_name)
                if values.contact_name
                else None
            ),
        )
        for channel in ("email", "sms", "whatsapp"):
            lead.eligibility.append(
                LeadChannelEligibility(channel=channel, state="needs_review")
            )
        lead.activity.append(
            Activity(
                type="lead.created",
                actor=actor,
                summary=f"Created manually by {actor}",
                details={"source": source, "entry_method": "manual"},
                created_at=created_at,
            )
        )
        lead.activity.append(
            Activity(
                type="lead.researched",
                actor=actor,
                summary=RESEARCH_ACTIVITY_SUMMARY.format(
                    website_status=website_status or NO_RESEARCH_SUMMARY
                ),
                details={"source": source, "entry_method": "manual"},
                created_at=created_at + timedelta(seconds=30),
            )
        )
        self.repository.add(lead)

        try:
            self.repository.flush()
        except IntegrityError as exc:
            self.repository.session.rollback()
            raise LeadConflictError(
                "A lead with this phone number already exists."
            ) from exc

        ComplianceEvaluator(self.repository).evaluate(
            lead,
            actor=actor,
            record_activity=False,
        )
        try:
            self.repository.commit()
        except IntegrityError as exc:
            self.repository.session.rollback()
            raise LeadConflictError(
                "A lead with this phone number already exists."
            ) from exc

        saved = self.repository.get_with_activity(lead.id)
        if saved is None:  # pragma: no cover - the commit just created it
            raise LeadNotFoundError(str(lead.id))
        return saved

    @staticmethod
    def _parse_id(lead_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(lead_id)
        except (ValueError, AttributeError, TypeError) as exc:
            # Not a uuid, so it cannot be a lead we hold.
            raise LeadNotFoundError(lead_id) from exc
