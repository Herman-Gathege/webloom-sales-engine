"""Approved policy matching is explicit, versioned, and fail-closed."""

import json
from datetime import date

import pytest

from app.config import get_settings
from app.models import LeadProvenance
from app.services.compliance_policy import (
    CompliancePolicy,
    CompliancePolicyError,
    CompliancePolicyRegistry,
    load_default_policy_registry,
)


def approved_email_policy(**overrides: object) -> CompliancePolicy:
    values: dict[str, object] = {
        "id": "synthetic-google-maps-email",
        "version": "1",
        "channel": "email",
        "source": "google_maps",
        "intended_purpose": "Business outreach",
        "contact_types": frozenset({"generic_business"}),
        "collection_methods": frozenset({"Manual listing review"}),
        "required_provenance_fields": frozenset(
            {
                "source",
                "source_name",
                "source_url",
                "collection_date",
                "collection_method",
                "intended_purpose",
                "contact_type",
            }
        ),
        "lawful_basis": "legitimate_interests",
        "rationale": "Synthetic test policy only.",
        "approved_by": "compliance@example.test",
        "approved_at": date(2026, 11, 9),
        "approval_reference": "SYNTHETIC-ONLY",
    }
    values.update(overrides)
    return CompliancePolicy(**values)


def add_complete_provenance(lead) -> None:
    lead.provenance = LeadProvenance(
        source_name="Google Maps listing",
        source_url="https://example.test/business",
        collection_date=date(2026, 11, 1),
        collection_method="Manual listing review",
        intended_purpose="Business outreach",
        contact_type="generic_business",
    )


def registry(*policies: CompliancePolicy) -> CompliancePolicyRegistry:
    return CompliancePolicyRegistry(
        version="synthetic-policy-set-1",
        policies=tuple(policies),
    )


def policy_mapping(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "schema_version": 1,
        "version": "1",
        "policies": [
            {
                "id": "synthetic-rule",
                "version": "1",
                "channel": "email",
                "source": "google_maps",
                "intended_purpose": "Business outreach",
                "contact_types": ["generic_business"],
                "collection_methods": ["Manual listing review"],
                "required_provenance_fields": ["source_url"],
                "lawful_basis": "legitimate_interests",
                "rationale": "Synthetic test policy only.",
                "approved_by": "compliance@example.test",
                "approved_at": "2026-11-09",
                "approval_reference": "SYNTHETIC-ONLY",
                "enabled": True,
            }
        ],
    }
    first_policy = values["policies"][0]
    assert isinstance(first_policy, dict)
    first_policy.update(overrides)
    return values


def test_an_empty_registry_never_approves_a_channel(make_lead) -> None:
    lead = make_lead(email="owner@example.test")
    add_complete_provenance(lead)

    decision = registry().evaluate(lead, "email")

    assert decision.status == "needs_review"
    assert decision.policy is None
    assert decision.reason_codes == ("no_approved_policy:email",)


def test_committed_policy_is_the_approved_sms_rule() -> None:
    registry = load_default_policy_registry()

    assert registry.version == "2026-11-09.1"
    assert len(registry.policies) == 1
    policy = registry.policies[0]
    assert policy.id == "yellow-pages-generic-business-sms-v1"
    assert policy.channel == "sms"
    assert policy.source == "yellow_pages_kenya_listing"
    assert policy.lawful_basis == "legitimate_interests"
    assert policy.enabled is True


def test_configured_policy_path_is_loaded(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "approved-policy.json"
    payload = policy_mapping()
    payload["version"] = "configured-1"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("COMPLIANCE_POLICY_PATH", str(path))
    get_settings.cache_clear()
    load_default_policy_registry.cache_clear()

    try:
        registry = load_default_policy_registry()
        assert registry.version == "configured-1"
    finally:
        get_settings.cache_clear()
        load_default_policy_registry.cache_clear()


def test_an_enabled_policy_can_qualify_a_channel(make_lead) -> None:
    lead = make_lead(email="owner@example.test")
    add_complete_provenance(lead)

    decision = registry(approved_email_policy()).evaluate(lead, "email")

    assert decision.status == "eligible"
    assert decision.policy is not None
    assert decision.policy.id == "synthetic-google-maps-email"
    assert decision.reason_codes == ("automated_policy_eligible:email",)
    assert "source_url" in decision.evidence_references


def test_policy_scope_mismatch_remains_an_exception(make_lead) -> None:
    lead = make_lead(email="owner@example.test")
    add_complete_provenance(lead)
    lead.provenance.intended_purpose = "Recruitment"

    decision = registry(approved_email_policy()).evaluate(lead, "email")

    assert decision.status == "needs_review"
    assert decision.policy is None
    assert decision.reason_codes == ("policy_context_not_met:email",)


def test_missing_policy_required_evidence_remains_an_exception(make_lead) -> None:
    lead = make_lead(email="owner@example.test")
    add_complete_provenance(lead)
    lead.provenance.source_url = None

    decision = registry(approved_email_policy()).evaluate(lead, "email")

    assert decision.status == "needs_review"
    assert decision.policy is not None
    assert decision.reason_codes == ("policy_evidence_insufficient:email",)


def test_disabled_policy_is_ignored(make_lead) -> None:
    lead = make_lead(email="owner@example.test")
    add_complete_provenance(lead)

    decision = registry(approved_email_policy(enabled=False)).evaluate(lead, "email")

    assert decision.status == "needs_review"
    assert decision.reason_codes == ("no_approved_policy:email",)


def test_policy_file_rejects_an_unapproved_rule(tmp_path) -> None:
    path = tmp_path / "policy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "version": "1",
                "policies": [
                    {
                        "id": "missing-approval",
                        "version": "1",
                        "channel": "email",
                        "source": "google_maps",
                        "intended_purpose": "Business outreach",
                        "contact_types": ["generic_business"],
                        "collection_methods": ["Manual listing review"],
                        "required_provenance_fields": ["source_url"],
                        "lawful_basis": "legitimate_interests",
                        "rationale": "Synthetic test policy only.",
                        "approved_by": "",
                        "approved_at": "2026-11-09",
                        "approval_reference": "SYNTHETIC-ONLY",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(CompliancePolicyError, match="approved_by"):
        CompliancePolicyRegistry.from_file(path)


@pytest.mark.parametrize("field", ["id", "channel", "lawful_basis", "approved_by"])
def test_policy_file_rejects_null_required_text(field: str) -> None:
    with pytest.raises(CompliancePolicyError, match=field):
        CompliancePolicyRegistry.from_mapping(policy_mapping(**{field: None}))


def test_policy_file_rejects_string_instead_of_enabled_boolean() -> None:
    with pytest.raises(CompliancePolicyError, match="enabled"):
        CompliancePolicyRegistry.from_mapping(policy_mapping(enabled="false"))

