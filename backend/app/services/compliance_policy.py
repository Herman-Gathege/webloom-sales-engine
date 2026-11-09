"""Versioned, fail-closed outreach policy evaluation.

The policy file records organisation-level decisions. It never contains lead
contact data, reviewer identities for individual leads, or inferred evidence.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.config import get_settings
from app.models import Lead, LeadProvenance

CHANNELS = frozenset({"email", "sms", "whatsapp"})
LAWFUL_BASES = frozenset(
    {
        "consent",
        "contract",
        "legal_obligation",
        "vital_interests",
        "public_interest",
        "legitimate_interests",
        "research_statistics",
    }
)
CONTACT_TYPES = frozenset({"unknown", "generic_business", "named_individual"})
PROVENANCE_FIELDS = frozenset(
    {
        "source",
        "source_name",
        "source_url",
        "collection_date",
        "collection_method",
        "intended_purpose",
        "contact_type",
    }
)

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "compliance_policy.json"
)


class CompliancePolicyError(ValueError):
    """The approved policy configuration is missing, malformed, or incomplete."""


@dataclass(frozen=True)
class CompliancePolicy:
    """One approved source, purpose, contact type and channel combination."""

    id: str
    version: str
    channel: str
    source: str
    intended_purpose: str
    contact_types: frozenset[str]
    collection_methods: frozenset[str]
    required_provenance_fields: frozenset[str]
    lawful_basis: str
    rationale: str
    approved_by: str
    approved_at: date
    approval_reference: str
    enabled: bool = True

    def __post_init__(self) -> None:
        required_text = {
            "id": self.id,
            "version": self.version,
            "source": self.source,
            "intended_purpose": self.intended_purpose,
            "lawful_basis": self.lawful_basis,
            "rationale": self.rationale,
            "approved_by": self.approved_by,
            "approval_reference": self.approval_reference,
        }
        for field, value in required_text.items():
            if not value or not value.strip():
                raise CompliancePolicyError(f"Policy field {field!r} must not be blank.")
        if self.channel not in CHANNELS:
            raise CompliancePolicyError(
                f"Policy channel {self.channel!r} must be one of {sorted(CHANNELS)}."
            )
        if self.lawful_basis not in LAWFUL_BASES:
            raise CompliancePolicyError(
                f"Policy lawful_basis {self.lawful_basis!r} is not a documented category."
            )
        if not self.contact_types or not self.contact_types <= CONTACT_TYPES:
            raise CompliancePolicyError(
                "Policy contact_types must be a non-empty subset of "
                f"{sorted(CONTACT_TYPES)}."
            )
        if not self.collection_methods or any(
            not value.strip() for value in self.collection_methods
        ):
            raise CompliancePolicyError(
                "Policy collection_methods must contain at least one non-blank value."
            )
        if (
            not self.required_provenance_fields
            or not self.required_provenance_fields <= PROVENANCE_FIELDS
        ):
            raise CompliancePolicyError(
                "Policy required_provenance_fields must be a non-empty subset of "
                f"{sorted(PROVENANCE_FIELDS)}."
            )
        if not isinstance(self.approved_at, date):
            raise CompliancePolicyError("Policy approved_at must be a date.")


@dataclass(frozen=True)
class AutomatedPolicyDecision:
    """The policy result for one lead and one channel."""

    status: Literal["eligible", "needs_review"]
    policy: CompliancePolicy | None
    reason_codes: tuple[str, ...]
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class CompliancePolicyRegistry:
    """The complete approved policy set used by the evaluator."""

    version: str
    policies: tuple[CompliancePolicy, ...]

    def __post_init__(self) -> None:
        if not self.version or not self.version.strip():
            raise CompliancePolicyError("Policy set version must not be blank.")
        ids = [policy.id for policy in self.policies]
        if len(ids) != len(set(ids)):
            raise CompliancePolicyError("Policy ids must be unique within the policy set.")

    @property
    def fingerprint(self) -> str:
        payload = {
            "version": self.version,
            "policies": [
                {
                    "id": policy.id,
                    "version": policy.version,
                    "channel": policy.channel,
                    "source": policy.source,
                    "intended_purpose": policy.intended_purpose,
                    "contact_types": sorted(policy.contact_types),
                    "collection_methods": sorted(policy.collection_methods),
                    "required_provenance_fields": sorted(
                        policy.required_provenance_fields
                    ),
                    "lawful_basis": policy.lawful_basis,
                    "rationale": policy.rationale,
                    "approved_by": policy.approved_by,
                    "approved_at": policy.approved_at.isoformat(),
                    "approval_reference": policy.approval_reference,
                    "enabled": policy.enabled,
                }
                for policy in sorted(self.policies, key=lambda item: item.id)
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()

    def evaluate(self, lead: Lead, channel: str) -> AutomatedPolicyDecision:
        """Apply only enabled policies whose complete documented scope matches."""
        candidates = [
            policy
            for policy in self.policies
            if policy.enabled
            and policy.channel == channel
            and policy.source == lead.source
        ]
        if not candidates:
            return AutomatedPolicyDecision(
                status="needs_review",
                policy=None,
                reason_codes=(f"no_approved_policy:{channel}",),
                evidence_references=(),
            )

        provenance = lead.provenance
        if provenance is None:
            return AutomatedPolicyDecision(
                status="needs_review",
                policy=None,
                reason_codes=(f"policy_context_not_met:{channel}",),
                evidence_references=(),
            )

        context_matches = [
            policy
            for policy in candidates
            if provenance.intended_purpose == policy.intended_purpose
            and provenance.contact_type in policy.contact_types
            and provenance.collection_method in policy.collection_methods
        ]
        if not context_matches:
            return AutomatedPolicyDecision(
                status="needs_review",
                policy=None,
                reason_codes=(f"policy_context_not_met:{channel}",),
                evidence_references=(),
            )

        evidence = self._evidence_references(lead, provenance)
        for policy in context_matches:
            if policy.required_provenance_fields <= evidence:
                return AutomatedPolicyDecision(
                    status="eligible",
                    policy=policy,
                    reason_codes=(f"automated_policy_eligible:{channel}",),
                    evidence_references=tuple(sorted(evidence)),
                )

        return AutomatedPolicyDecision(
            status="needs_review",
            policy=context_matches[0],
            reason_codes=(f"policy_evidence_insufficient:{channel}",),
            evidence_references=tuple(sorted(evidence)),
        )

    @classmethod
    def from_file(cls, path: Path = DEFAULT_POLICY_PATH) -> "CompliancePolicyRegistry":
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CompliancePolicyError(
                f"Compliance policy file does not exist: {path}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise CompliancePolicyError(
                f"Compliance policy file could not be read: {path}"
            ) from exc
        return cls.from_mapping(raw)

    @classmethod
    def from_mapping(cls, raw: object) -> "CompliancePolicyRegistry":
        if not isinstance(raw, dict):
            raise CompliancePolicyError("Compliance policy file must contain an object.")
        if raw.get("schema_version") != 1:
            raise CompliancePolicyError("Compliance policy schema_version must be 1.")
        policies_raw = raw.get("policies")
        if not isinstance(policies_raw, list):
            raise CompliancePolicyError("Compliance policy policies must be a list.")

        try:
            policies = tuple(_policy_from_mapping(item) for item in policies_raw)
            return cls(version=str(raw["version"]), policies=policies)
        except KeyError as exc:
            raise CompliancePolicyError(
                f"Compliance policy is missing field {exc.args[0]!r}."
            ) from exc
        except (TypeError, ValueError) as exc:
            if isinstance(exc, CompliancePolicyError):
                raise
            raise CompliancePolicyError(f"Compliance policy is malformed: {exc}") from exc

    @staticmethod
    def _evidence_references(lead: Lead, provenance: LeadProvenance) -> set[str]:
        values = {
            "source": lead.source,
            "source_name": provenance.source_name,
            "source_url": provenance.source_url,
            "collection_date": provenance.collection_date,
            "collection_method": provenance.collection_method,
            "intended_purpose": provenance.intended_purpose,
            "contact_type": provenance.contact_type,
        }
        return {
            field
            for field, value in values.items()
            if value is not None and str(value).strip()
        }


def _policy_from_mapping(raw: object) -> CompliancePolicy:
    if not isinstance(raw, dict):
        raise CompliancePolicyError("Each compliance policy must be an object.")
    required_text = {
        field: _required_policy_string(raw, field)
        for field in (
            "id",
            "version",
            "channel",
            "source",
            "intended_purpose",
            "lawful_basis",
            "rationale",
            "approved_by",
            "approval_reference",
        )
    }
    approved_at = raw.get("approved_at")
    if not isinstance(approved_at, str):
        raise CompliancePolicyError("Policy approved_at must be an ISO date.")
    try:
        parsed_approved_at = date.fromisoformat(approved_at)
    except ValueError as exc:
        raise CompliancePolicyError("Policy approved_at must be an ISO date.") from exc

    contact_types = _policy_string_set(raw, "contact_types")
    collection_methods = _policy_string_set(raw, "collection_methods")
    required_fields = _policy_string_set(raw, "required_provenance_fields")
    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        raise CompliancePolicyError("Policy enabled must be true or false.")

    return CompliancePolicy(
        id=required_text["id"],
        version=required_text["version"],
        channel=required_text["channel"],
        source=required_text["source"],
        intended_purpose=required_text["intended_purpose"],
        contact_types=contact_types,
        collection_methods=collection_methods,
        required_provenance_fields=required_fields,
        lawful_basis=required_text["lawful_basis"],
        rationale=required_text["rationale"],
        approved_by=required_text["approved_by"],
        approved_at=parsed_approved_at,
        approval_reference=required_text["approval_reference"],
        enabled=enabled,
    )


def _required_policy_string(raw: dict[str, object], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CompliancePolicyError(f"Policy field {field!r} must not be blank.")
    return value


def _policy_string_set(raw: dict[str, object], field: str) -> frozenset[str]:
    value = raw.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise CompliancePolicyError(f"Policy {field} must be a list of strings.")
    return frozenset(value)


@lru_cache(maxsize=1)
def load_default_policy_registry() -> CompliancePolicyRegistry:
    """Load the repository policy file; an empty set is safe and approves nobody."""
    configured_path = get_settings().compliance_policy_path
    path = Path(configured_path).expanduser() if configured_path else DEFAULT_POLICY_PATH
    return CompliancePolicyRegistry.from_file(path)

