"""Deterministic automatic compliance evaluation for one lead.

The human decision remains in `lead_channel_eligibility`. This service derives
the latest lead-level result from those decisions, provenance, technical contact
availability, and terminal suppression. It never treats a public contact or a
valid address as permission to market.
"""

import hashlib
import json
import re
from datetime import UTC, date, datetime

from app.models import (
    Activity,
    Lead,
    LeadChannelEligibility,
    LeadComplianceEvaluation,
)
from app.repositories import LeadRepository
from app.services.contact_identity import contact_fingerprint, valid_email

RULE_VERSION = "2026-10-27.1"
CHANNELS = ("email", "sms", "whatsapp")

_REASON_TEXT = {
    "business_name_missing": "the business name is missing",
    "no_usable_contact": "there is no usable contact",
    "invalid_phone": "the phone number is not usable",
    "invalid_email": "the email address is not usable",
    "missing_provenance": "source or provenance is missing",
    "incomplete_provenance": "source or provenance is incomplete",
    "all_marketing_suppressed": "all marketing is suppressed",
    "lead_opted_out": "the lead is marked opted out",
    "all_available_channels_suppressed": "every available channel is suppressed",
}


class ComplianceEvaluator:
    """Evaluate and persist the current compliance snapshot for a lead."""

    def __init__(self, repository: LeadRepository | None = None) -> None:
        self.repository = repository

    def evaluate(
        self,
        lead: Lead,
        *,
        actor: str = "system",
        record_activity: bool = True,
        force: bool = False,
    ) -> LeadComplianceEvaluation:
        """Return the current snapshot, reusing it when the inputs are unchanged."""
        self._load_suppressions(lead)
        fingerprint = self.input_fingerprint(lead)
        current = lead.compliance
        if (
            not force
            and current is not None
            and current.rule_version == RULE_VERSION
            and current.input_fingerprint == fingerprint
        ):
            return current

        result = self._build(lead, fingerprint)
        previous_status = current.status if current is not None else None
        previous_reasons = current.reason_codes if current is not None else []

        evaluation = current or LeadComplianceEvaluation(lead=lead)
        evaluation.status = result["status"]
        evaluation.data_quality_status = result["data_quality_status"]
        evaluation.reason_codes = result["reason_codes"]
        evaluation.explanation = result["explanation"]
        evaluation.eligible_channels = result["eligible_channels"]
        evaluation.suppressed_channels = result["suppressed_channels"]
        evaluation.channel_results = result["channel_results"]
        evaluation.outreach_ready = result["outreach_ready"]
        evaluation.evaluated_at = datetime.now(UTC)
        evaluation.rule_version = RULE_VERSION
        evaluation.input_fingerprint = fingerprint
        lead.compliance = evaluation

        if current is None and self.repository is not None:
            self.repository.add(evaluation)

        changed = (
            previous_status != evaluation.status
            or previous_reasons != evaluation.reason_codes
        )
        if record_activity and (current is None or changed):
            activity = Activity(
                lead_id=lead.id,
                type="lead.compliance_evaluated",
                actor=actor,
                summary=(
                    "Compliance evaluated: "
                    f"{evaluation.status.replace('_', ' ')}"
                ),
                details={
                    "previous_status": previous_status,
                    "status": evaluation.status,
                    "data_quality_status": evaluation.data_quality_status,
                    "reason_codes": evaluation.reason_codes,
                    "eligible_channels": evaluation.eligible_channels,
                    "rule_version": evaluation.rule_version,
                },
            )
            if self.repository is None:
                lead.activity.append(activity)
            else:
                self.repository.add_activity(activity)
        return evaluation

    def review_blocker(self, lead: Lead, channel: str) -> str | None:
        """Return the reason an eligible human decision cannot be recorded."""
        if not self._technical_available(lead, channel):
            return (
                f"{channel.upper()} cannot be approved because the lead has no "
                f"usable {channel.upper()} contact."
            )
        if not self.provenance_sufficient(lead):
            return (
                "Source/provenance information is required before this channel "
                "can be approved for outreach."
            )
        return None

    def input_fingerprint(self, lead: Lead) -> str:
        """Hash every fact that can materially change eligibility."""
        channels = {
            channel: self.channel_input_fingerprint(lead, channel)
            for channel in CHANNELS
        }
        payload = {
            "rule_version": RULE_VERSION,
            "business_name": self._clean(lead.business_name),
            "phone": self._clean(lead.phone),
            "email": self._clean(lead.email),
            "whatsapp_capable": lead.whatsapp_capable,
            "source": self._clean(lead.source),
            "status": lead.status.value if hasattr(lead.status, "value") else lead.status,
            "provenance": self._provenance_payload(lead),
            "channels": channels,
            "suppressions": self._suppression_payload(lead),
        }
        return self._hash(payload)

    def channel_input_fingerprint(
        self,
        lead: Lead,
        channel_or_record: str | LeadChannelEligibility,
    ) -> str:
        """Hash the contact, provenance, suppression, and review for one channel."""
        channel = (
            channel_or_record
            if isinstance(channel_or_record, str)
            else channel_or_record.channel
        )
        review = (
            next(
                (record for record in lead.eligibility if record.channel == channel),
                None,
            )
            if isinstance(channel_or_record, str)
            else channel_or_record
        )
        payload = {
            "rule_version": RULE_VERSION,
            "channel": channel,
            "business_name": self._clean(lead.business_name),
            "contact": (
                self._clean(lead.email)
                if channel == "email"
                else self._clean(lead.phone)
            ),
            "whatsapp_capable": (
                lead.whatsapp_capable if channel == "whatsapp" else None
            ),
            "source": self._clean(lead.source),
            "provenance": self._provenance_payload(lead),
            "suppressions": [
                row
                for row in self._suppression_payload(lead)
                if row["scope"] in {"all_marketing", channel}
            ],
            "review": self._review_payload(review),
        }
        return self._hash(payload)

    @staticmethod
    def provenance_sufficient(lead: Lead) -> bool:
        provenance = lead.provenance
        if provenance is None or not (lead.source and lead.source.strip()):
            return False
        return any(
            value and value.strip()
            for value in (
                provenance.source_name,
                provenance.source_url,
                provenance.collection_method,
            )
        )

    @staticmethod
    def review_complete(record: LeadChannelEligibility) -> bool:
        return record.state == "eligible" and all(
            value and str(value).strip()
            for value in (
                record.lawful_basis,
                record.evidence_summary,
                record.evidence_source,
                record.intended_purpose,
                record.contact_context,
                record.reviewer,
                record.reviewed_at,
                record.rationale,
            )
        )

    def _build(self, lead: Lead, fingerprint: str) -> dict[str, object]:
        provenance_ok = self.provenance_sufficient(lead)
        business_ok = bool(lead.business_name and lead.business_name.strip())
        phone_ok = self._valid_phone(lead.phone)
        email_ok = bool(lead.email and valid_email(lead.email))
        any_contact = phone_ok or email_ok

        quality_reasons: list[str] = []
        if not business_ok:
            quality_reasons.append("business_name_missing")
        if not any_contact:
            quality_reasons.append("no_usable_contact")
        else:
            if lead.phone and not phone_ok:
                quality_reasons.append("invalid_phone")
            if lead.email and not email_ok:
                quality_reasons.append("invalid_email")

        if not any_contact or not business_ok:
            data_quality = "invalid"
        elif not provenance_ok or quality_reasons:
            data_quality = "incomplete"
        else:
            data_quality = "complete"

        review_by_channel = {record.channel: record for record in lead.eligibility}
        scopes = {record.scope for record in lead.matching_suppressions}
        all_marketing = "all_marketing" in scopes
        lead_opted_out = (
            lead.status.value if hasattr(lead.status, "value") else str(lead.status)
        ) == "opted_out"

        channel_results: list[dict[str, object]] = []
        eligible_channels: list[str] = []
        suppressed_channels: list[str] = []
        available_channels: list[str] = []
        all_reasons: list[str] = []

        for channel in CHANNELS:
            record = review_by_channel.get(channel)
            technical = self._technical_available(lead, channel)
            if technical:
                available_channels.append(channel)
            suppressed = all_marketing or channel in scopes
            if suppressed:
                suppressed_channels.append(channel)

            current_review = (
                record is not None
                and self.review_complete(record)
                and record.reviewed_input_fingerprint
                == self.channel_input_fingerprint(lead, channel)
            )
            channel_reasons: list[str] = []
            if suppressed:
                channel_status = "blocked"
                channel_reasons.append(f"suppressed:{channel}")
            elif not technical:
                channel_status = "invalid"
                channel_reasons.append(f"contact_unavailable:{channel}")
            elif not provenance_ok:
                channel_status = "needs_review"
                channel_reasons.extend(
                    ["missing_provenance"]
                    if lead.provenance is None
                    else ["incomplete_provenance"]
                )
            elif record is None or record.state != "eligible":
                channel_status = "needs_review"
                channel_reasons.append(f"human_review_required:{channel}")
            elif not self.review_complete(record):
                channel_status = "needs_review"
                channel_reasons.append(f"incomplete_review:{channel}")
            elif record.reviewed_input_fingerprint != self.channel_input_fingerprint(
                lead, channel
            ):
                channel_status = "needs_review"
                channel_reasons.append(f"review_stale:{channel}")
            else:
                channel_status = "eligible"
                channel_reasons.append(f"eligible:{channel}")

            if channel_status == "eligible":
                eligible_channels.append(channel)
            all_reasons.extend(channel_reasons)
            channel_results.append(
                {
                    "channel": channel,
                    "status": channel_status,
                    "technical_available": technical,
                    "decision_current": current_review,
                    "reason_codes": sorted(set(channel_reasons)),
                    "explanation": self._channel_explanation(
                        channel, channel_status, channel_reasons
                    ),
                }
            )

        if lead_opted_out or all_marketing:
            status = "blocked"
            reason_codes = (
                ["lead_opted_out"] if lead_opted_out else ["all_marketing_suppressed"]
            )
        elif not business_ok or not any_contact:
            status = "invalid"
            reason_codes = quality_reasons or ["no_usable_contact"]
        elif eligible_channels:
            status = "eligible"
            reason_codes = [f"eligible:{channel}" for channel in eligible_channels]
            reason_codes.extend(
                f"suppressed:{channel}" for channel in suppressed_channels
            )
        elif available_channels and set(available_channels) <= set(suppressed_channels):
            status = "blocked"
            reason_codes = ["all_available_channels_suppressed"]
        else:
            status = "needs_review"
            reason_codes = all_reasons
            if not provenance_ok:
                reason_codes.append(
                    "missing_provenance"
                    if lead.provenance is None
                    else "incomplete_provenance"
                )
            if quality_reasons:
                reason_codes.extend(quality_reasons)

        reason_codes = sorted(set(reason_codes))
        explanation = self._explanation(
            status,
            data_quality,
            reason_codes,
            eligible_channels,
            suppressed_channels,
        )
        return {
            "status": status,
            "data_quality_status": data_quality,
            "reason_codes": reason_codes,
            "explanation": explanation,
            "eligible_channels": eligible_channels,
            "suppressed_channels": suppressed_channels,
            "channel_results": channel_results,
            "outreach_ready": status == "eligible" and bool(eligible_channels),
            "input_fingerprint": fingerprint,
        }

    @staticmethod
    def _technical_available(lead: Lead, channel: str) -> bool:
        if channel == "email":
            return bool(lead.email and valid_email(lead.email))
        if not lead.phone or not ComplianceEvaluator._valid_phone(lead.phone):
            return False
        if channel == "whatsapp":
            return bool(lead.whatsapp_capable)
        return not (
            lead.phone.startswith("+254")
            and len(lead.phone) > 4
            and lead.phone[4] in "23456"
        )

    @staticmethod
    def _valid_phone(value: str | None) -> bool:
        return bool(value and re.fullmatch(r"\+254\d{9}", value))

    def _suppression_payload(self, lead: Lead) -> list[dict[str, str]]:
        return sorted(
            (
                {
                    "scope": record.scope,
                    "kind": record.contact_kind,
                    "fingerprint": record.contact_fingerprint,
                    "reason": record.reason,
                }
                for record in lead.matching_suppressions
            ),
            key=lambda item: (item["scope"], item["kind"], item["fingerprint"]),
        )

    def _load_suppressions(self, lead: Lead) -> None:
        """Load contact-independent restrictions when a repository is available."""
        if self.repository is None:
            return
        fingerprints: set[str] = set()
        if lead.phone:
            fingerprints.add(contact_fingerprint("phone", lead.phone))
        if lead.email:
            fingerprints.add(contact_fingerprint("email", lead.email))
        lead._matching_suppressions = self.repository.suppressions_for_fingerprints(
            fingerprints,
            lead_id=lead.id if lead.id is not None else None,
        )

    @staticmethod
    def _review_payload(
        record: LeadChannelEligibility | None,
    ) -> dict[str, object] | None:
        if record is None:
            return None
        return {
            "state": record.state,
            "lawful_basis": record.lawful_basis,
            "evidence_summary": record.evidence_summary,
            "evidence_source": record.evidence_source,
            "intended_purpose": record.intended_purpose,
            "contact_context": record.contact_context,
            "reviewer": record.reviewer,
            "reviewed_at": record.reviewed_at.isoformat() if record.reviewed_at else None,
            "rationale": record.rationale,
        }

    @staticmethod
    def _provenance_payload(lead: Lead) -> dict[str, object] | None:
        provenance = lead.provenance
        if provenance is None:
            return None
        return {
            "source_name": provenance.source_name,
            "source_url": provenance.source_url,
            "collection_date": (
                provenance.collection_date.isoformat()
                if isinstance(provenance.collection_date, date)
                else provenance.collection_date
            ),
            "collection_method": provenance.collection_method,
            "intended_purpose": provenance.intended_purpose,
            "contact_type": provenance.contact_type,
        }

    @staticmethod
    def _hash(payload: object) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode()).hexdigest()

    @staticmethod
    def _clean(value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None

    @staticmethod
    def _channel_explanation(
        channel: str, status: str, reasons: list[str]
    ) -> str:
        if status == "eligible":
            return f"{channel.upper()} has a current recorded basis for outreach."
        if status == "blocked":
            return f"{channel.upper()} is blocked by a terminal restriction."
        if status == "invalid":
            return f"{channel.upper()} has no technically usable contact."
        if any(reason.startswith("review_stale") for reason in reasons):
            return f"{channel.upper()} evidence is stale after an input changed."
        if any(reason.startswith("incomplete_review") for reason in reasons):
            return f"{channel.upper()} review evidence is incomplete."
        if "missing_provenance" in reasons or "incomplete_provenance" in reasons:
            return f"{channel.upper()} needs source or provenance review."
        return f"{channel.upper()} needs a human decision before outreach."

    @staticmethod
    def _explanation(
        status: str,
        data_quality: str,
        reasons: list[str],
        eligible_channels: list[str],
        suppressed_channels: list[str],
    ) -> str:
        readable = [_REASON_TEXT.get(reason, reason.replace(":", " ")) for reason in reasons]
        if status == "eligible":
            channels = ", ".join(eligible_channels)
            text = f"Outreach-ready on {channels}; recorded evidence is current."
            if suppressed_channels:
                text += (
                    " Suppressed channels remain blocked: "
                    + ", ".join(suppressed_channels)
                    + "."
                )
            return text
        if status == "blocked":
            return "Blocked: " + "; ".join(dict.fromkeys(readable)) + "."
        if status == "invalid":
            return (
                "Invalid or incomplete data: "
                + "; ".join(dict.fromkeys(readable))
                + "."
            )
        text = "Needs review: " + "; ".join(dict.fromkeys(readable)) + "."
        if data_quality == "incomplete":
            text += " Data quality is incomplete."
        return text
