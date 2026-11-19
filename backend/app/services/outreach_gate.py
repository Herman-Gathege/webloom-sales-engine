"""The single eligibility boundary future outreach actions must call."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.repositories import LeadRepository
from app.services.compliance_evaluator import ComplianceEvaluator
from app.services.compliance_policy import CompliancePolicyRegistry
from app.services.lead_service import LeadNotFoundError


@dataclass(frozen=True)
class OutreachGateResult:
    lead_id: uuid.UUID
    channel: str
    allowed: bool
    compliance_status: str
    channel_status: str | None
    technical_available: bool
    decision_current: bool
    decision_type: str
    policy_id: str | None
    policy_version: str | None
    policy_fingerprint: str | None
    policy_approved_by: str | None
    policy_approval_reference: str | None
    evidence_references: list[str]
    input_fingerprint: str | None
    reason_codes: list[str]
    explanation: str
    evaluated_at: datetime


class OutreachGateService:
    """Re-evaluate immediately and allow only a current channel approval."""

    def __init__(
        self,
        repository: LeadRepository,
        *,
        policy_registry: CompliancePolicyRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.evaluator = ComplianceEvaluator(
            repository,
            policy_registry=policy_registry,
        )

    def check(self, lead_id: str, channel: str, *, actor: str) -> OutreachGateResult:
        parsed_id = self._parse_id(lead_id)
        result = self._check(parsed_id, channel, actor=actor)
        self.repository.commit()
        return result

    def check_many(
        self,
        lead_ids: list[uuid.UUID],
        channel: str,
        *,
        actor: str,
        commit: bool = True,
    ) -> list[OutreachGateResult]:
        results = [
            self._check(lead_id, channel, actor=actor)
            for lead_id in lead_ids
        ]
        if commit:
            self.repository.commit()
        return results

    def _check(
        self, lead_id: uuid.UUID, channel: str, *, actor: str
    ) -> OutreachGateResult:
        lead = self.repository.get_with_activity(lead_id)
        if lead is None:
            raise LeadNotFoundError(str(lead_id))

        evaluation = self.evaluator.evaluate(
            lead,
            actor=actor,
            record_activity=True,
            force=True,
        )
        channel_result = next(
            (
                item
                for item in evaluation.channel_results
                if item.get("channel") == channel
            ),
            None,
        )
        allowed = (
            evaluation.status == "eligible"
            and channel in evaluation.eligible_channels
            and channel_result is not None
            and channel_result.get("status") == "eligible"
            and channel_result.get("decision_current") is True
        )
        if allowed:
            reason_codes = [f"eligible:{channel}"]
            explanation = (
                f"{channel.upper()} has a current recorded basis and can proceed "
                "to the approved outreach workflow."
            )
        elif channel_result is not None:
            reason_codes = list(channel_result.get("reason_codes", []))
            explanation = str(channel_result.get("explanation", evaluation.explanation))
        else:
            reason_codes = list(evaluation.reason_codes)
            explanation = evaluation.explanation

        return OutreachGateResult(
            lead_id=lead.id,
            channel=channel,
            allowed=allowed,
            compliance_status=evaluation.status,
            channel_status=(
                str(channel_result.get("status"))
                if channel_result is not None and channel_result.get("status")
                else None
            ),
            technical_available=bool(
                channel_result.get("technical_available", False)
                if channel_result is not None
                else False
            ),
            decision_current=bool(
                channel_result.get("decision_current", False)
                if channel_result is not None
                else False
            ),
            decision_type=str(
                channel_result.get("decision_type", "none")
                if channel_result is not None
                else "none"
            ),
            policy_id=(
                str(channel_result["policy_id"])
                if channel_result is not None and channel_result.get("policy_id")
                else None
            ),
            policy_version=(
                str(channel_result["policy_version"])
                if channel_result is not None and channel_result.get("policy_version")
                else None
            ),
            policy_fingerprint=(
                str(channel_result["policy_fingerprint"])
                if channel_result is not None
                and channel_result.get("policy_fingerprint")
                else None
            ),
            policy_approved_by=(
                str(channel_result["policy_approved_by"])
                if channel_result is not None
                and channel_result.get("policy_approved_by")
                else None
            ),
            policy_approval_reference=(
                str(channel_result["policy_approval_reference"])
                if channel_result is not None
                and channel_result.get("policy_approval_reference")
                else None
            ),
            evidence_references=[
                str(value)
                for value in (
                    channel_result.get("evidence_references", [])
                    if channel_result is not None
                    else []
                )
            ],
            input_fingerprint=(
                str(channel_result["input_fingerprint"])
                if channel_result is not None and channel_result.get("input_fingerprint")
                else None
            ),
            reason_codes=reason_codes,
            explanation=explanation,
            evaluated_at=evaluation.evaluated_at,
        )

    @staticmethod
    def _parse_id(value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as exc:
            raise LeadNotFoundError(value) from exc
