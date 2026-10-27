"""Human eligibility decisions and terminal marketing suppressions."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.models import Activity, Lead, LeadChannelEligibility, Suppression
from app.repositories import LeadRepository
from app.services.contact_identity import contact_fingerprint
from app.services.lead_service import LeadNotFoundError


@dataclass(frozen=True)
class EligibilityDecision:
    state: str
    lawful_basis: str | None
    evidence_summary: str | None
    evidence_source: str | None
    intended_purpose: str | None
    contact_context: str | None
    reviewer: str
    rationale: str


@dataclass(frozen=True)
class SuppressionDecision:
    scope: str
    reason: str
    source: str
    recorded_by: str
    note: str | None


class ComplianceTargetError(Exception):
    """The requested review or suppression cannot apply to this lead."""


class ComplianceService:
    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def review_eligibility(
        self,
        lead_id: str,
        channel: str,
        decision: EligibilityDecision,
    ) -> Lead:
        parsed_id = self._lead_id(lead_id)
        lead = self.repository.get_with_activity(parsed_id)
        if lead is None:
            raise LeadNotFoundError(lead_id)

        if any(
            suppression.scope in {"all_marketing", channel}
            for suppression in lead.matching_suppressions
        ):
            raise ComplianceTargetError(
                "Suppression is terminal; this channel's eligibility cannot be changed."
            )

        eligibility = self.repository.get_eligibility(parsed_id, channel)
        if eligibility is None:
            eligibility = LeadChannelEligibility(
                lead_id=parsed_id,
                channel=channel,
                state="needs_review",
            )
            self.repository.add_eligibility(eligibility)

        previous_state = eligibility.state
        eligibility.state = decision.state
        eligibility.lawful_basis = self._clean(decision.lawful_basis)
        eligibility.evidence_summary = self._clean(decision.evidence_summary)
        eligibility.evidence_source = self._clean(decision.evidence_source)
        eligibility.intended_purpose = self._clean(decision.intended_purpose)
        eligibility.contact_context = self._clean(decision.contact_context)
        eligibility.reviewer = decision.reviewer.strip()
        eligibility.reviewed_at = datetime.now(UTC)
        eligibility.rationale = decision.rationale.strip()

        self.repository.add_activity(
            Activity(
                lead_id=parsed_id,
                type="lead.eligibility_reviewed",
                actor=eligibility.reviewer,
                summary=f"{channel.upper()} eligibility marked {decision.state.replace('_', ' ')}",
                details={
                    "channel": channel,
                    "previous_state": previous_state,
                    "new_state": decision.state,
                    "lawful_basis": decision.lawful_basis,
                    "rationale": decision.rationale.strip(),
                },
            )
        )
        self.repository.commit()
        return self._reload(parsed_id)

    def record_suppression(self, lead_id: str, request: SuppressionDecision) -> Lead:
        parsed_id = self._lead_id(lead_id)
        lead = self.repository.get(parsed_id)
        if lead is None:
            raise LeadNotFoundError(lead_id)

        contacts = self._contacts_for_scope(lead, request.scope)
        if not contacts:
            raise ComplianceTargetError(
                f"This lead has no contact available for {request.scope.replace('_', ' ')}."
            )

        fingerprints = {
            contact_fingerprint(kind, value) for kind, value in contacts
        }
        existing = {
            row.contact_fingerprint
            for row in self.repository.suppressions_for_fingerprints(fingerprints)
            if row.scope == request.scope
        }
        created = False
        for contact_kind, value in contacts:
            fingerprint = contact_fingerprint(contact_kind, value)
            if fingerprint in existing:
                continue
            self.repository.add_suppression(
                Suppression(
                    lead_id=parsed_id,
                    contact_fingerprint=fingerprint,
                    contact_kind=contact_kind,
                    scope=request.scope,
                    reason=request.reason,
                    source=request.source.strip(),
                    recorded_by=request.recorded_by.strip(),
                    note=self._clean(request.note),
                )
            )
            created = True

        if created:
            self.repository.add_activity(
                Activity(
                    lead_id=parsed_id,
                    type="lead.suppressed",
                    actor=request.recorded_by.strip(),
                    summary=(
                        f"Marketing restriction recorded: "
                        f"{request.scope.replace('_', ' ')}"
                    ),
                    details={
                        "scope": request.scope,
                        "reason": request.reason,
                        "contact_kinds": sorted({kind for kind, _ in contacts}),
                    },
                )
            )
            self.repository.commit()
        return self._reload(parsed_id)

    @staticmethod
    def _contacts_for_scope(lead: Lead, scope: str) -> list[tuple[str, str]]:
        phone = [("phone", lead.phone)] if lead.phone else []
        email = [("email", lead.email)] if lead.email else []
        if scope == "all_marketing":
            return [*phone, *email]
        if scope == "email":
            return email
        return phone

    def _reload(self, lead_id: uuid.UUID) -> Lead:
        lead = self.repository.get_with_activity(lead_id)
        if lead is None:  # pragma: no cover - protected by the pre-check
            raise LeadNotFoundError(str(lead_id))
        return lead

    @staticmethod
    def _lead_id(value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as exc:
            raise LeadNotFoundError(value) from exc

    @staticmethod
    def _clean(value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None
