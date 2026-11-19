"""Sprint 5 campaign preview, generation, archive and authorization behavior."""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.main import app
from app.models import (
    Lead,
    LeadProvenance,
    MessageTemplate,
    Offer,
    TemplateChannel,
    User,
    UserRole,
)


def add_policy_provenance(lead: Lead) -> None:
    lead.source = "yellow_pages_kenya_listing"
    lead.provenance = LeadProvenance(
        source_name="Yellow Pages Kenya listing",
        source_url=f"https://example.test/listings/{lead.id}",
        collection_date=date(2026, 11, 19),
        collection_method="Public business directory review",
        intended_purpose="Business outreach",
        contact_type="generic_business",
    )


def campaign_catalogue(
    session: Session,
    *,
    body: str = "Hi {{business_name}} from {{offer_name}}. {{opt_out}}",
) -> tuple[Offer, MessageTemplate]:
    offer = Offer(
        name="Starter Website",
        slug=f"starter-{uuid.uuid4().hex[:8]}",
        description="Synthetic offer",
        price_min=40000,
        price_max=None,
        currency="KES",
        pitch_angle="A useful website.",
        is_active=True,
    )
    template = MessageTemplate(
        offer=offer,
        channel=TemplateChannel.SMS,
        name="Synthetic SMS",
        variant="A",
        body=body,
        variables=[
            value
            for value in ("business_name", "offer_name", "opt_out")
            if f"{{{{{value}}}}}" in body
        ],
        is_active=True,
    )
    session.add_all([offer, template])
    session.flush()
    return offer, template


def campaign_payload(
    offer: Offer,
    template: MessageTemplate,
    lead_ids: list[uuid.UUID],
) -> dict[str, object]:
    return {
        "name": "Synthetic campaign",
        "goal": "Book five discovery calls with independent pharmacies.",
        "offer_id": str(offer.id),
        "template_id": str(template.id),
        "channel": "sms",
        "lead_ids": [str(value) for value in lead_ids],
        "selection_context": {
            "sector": "Pharmacies",
            "website": "no",
            "outreach_ready": True,
        },
    }


def test_preview_create_generate_and_idempotent_rerun(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    eligible = make_lead(business_name="Synthetic Eligible Pharmacy")
    add_policy_provenance(eligible)
    review_only = make_lead(
        business_name="Synthetic Review Clinic",
        source="manual_entry",
    )
    review_only.provenance = LeadProvenance(
        source_name="Manual seller entry",
        collection_date=date(2026, 11, 19),
        collection_method="Manual seller entry",
        intended_purpose="Business outreach",
        contact_type="generic_business",
    )
    session.add_all([eligible, review_only])
    session.flush()
    payload = campaign_payload(offer, template, [eligible.id, review_only.id])

    preview = client.post("/api/v1/campaigns/preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["eligible_count"] == 1
    assert preview.json()["skipped_count"] == 1
    assert preview.json()["eligible"][0]["research_stale"] is False
    assert preview.json()["eligible"][0]["source"] == "yellow_pages_kenya_listing"
    assert preview.json()["skipped"][0]["label"] == "Needs review"

    created = client.post("/api/v1/campaigns", json=payload)
    assert created.status_code == 201
    campaign = created.json()
    assert campaign["status"] == "draft"
    assert campaign["selected_count"] == 2
    assert campaign["drafts"] == []
    assert campaign["selection_context"] == {
        "sector": "Pharmacies",
        "website": "no",
        "outreach_ready": True,
    }
    assert campaign["events"][0]["event_type"] == "campaign.created"

    generated = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert generated.status_code == 200
    body = generated.json()
    assert body["status"] == "generated"
    assert body["draft_count"] == 1
    assert body["skip_count"] == 1
    assert body["drafts"][0]["state"] == "draft"
    assert body["drafts"][0]["rendered_body"].endswith("Reply STOP to opt out.")
    assert body["drafts"][0]["sms_encoding"] == "gsm-7"
    assert body["drafts"][0]["sms_segments"] == 1
    assert body["drafts"][0]["research_stale"] is False
    assert body["drafts"][0]["eligibility_snapshot"]["decision_type"] == (
        "automated_policy"
    )
    assert body["drafts"][0]["eligibility_snapshot"]["policy_id"] == (
        "yellow-pages-generic-business-sms-v1"
    )
    assert [event["event_type"] for event in body["events"]] == [
        "campaign.created",
        "campaign.generated",
    ]
    draft_id = body["drafts"][0]["id"]

    rerun = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert rerun.status_code == 200
    assert [row["id"] for row in rerun.json()["drafts"]] == [draft_id]


def test_archive_restore_and_generated_campaign_immutability(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(business_name="Synthetic Archive Pharmacy")
    add_policy_provenance(lead)
    session.add(lead)
    session.flush()
    payload = campaign_payload(offer, template, [lead.id])
    campaign = client.post("/api/v1/campaigns", json=payload).json()
    generated_response = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert generated_response.status_code == 200, generated_response.text
    generated = generated_response.json()
    assert generated["status"] == "generated"

    update = client.patch(f"/api/v1/campaigns/{campaign['id']}", json=payload)
    assert update.status_code == 409

    archived = client.post(f"/api/v1/campaigns/{campaign['id']}/archive")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert len(archived.json()["drafts"]) == len(generated["drafts"])
    blocked_rerun = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert blocked_rerun.status_code == 409

    listed = client.get("/api/v1/campaigns")
    assert campaign["id"] not in {row["id"] for row in listed.json()["items"]}
    archived_list = client.get("/api/v1/campaigns?include_archived=true")
    assert campaign["id"] in {row["id"] for row in archived_list.json()["items"]}

    restored = client.post(f"/api/v1/campaigns/{campaign['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["status"] == "generated"


def test_campaign_can_be_edited_before_generation(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    first = make_lead(business_name="Synthetic First Pharmacy")
    second = make_lead(business_name="Synthetic Second Pharmacy")
    add_policy_provenance(first)
    add_policy_provenance(second)
    session.add_all([first, second])
    session.flush()
    payload = campaign_payload(offer, template, [first.id])
    campaign = client.post("/api/v1/campaigns", json=payload).json()

    changed = dict(payload)
    changed.update(
        {
            "name": "Edited synthetic campaign",
            "goal": "Edited outcome goal.",
            "lead_ids": [str(second.id)],
        }
    )
    response = client.patch(f"/api/v1/campaigns/{campaign['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["name"] == "Edited synthetic campaign"
    assert response.json()["selected_lead_ids"] == [str(second.id)]
    assert [event["event_type"] for event in response.json()["events"]] == [
        "campaign.created",
        "campaign.updated",
    ]


def test_campaign_edit_preserves_an_unchanged_selected_lead(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(business_name="Synthetic Stable Pharmacy")
    add_policy_provenance(lead)
    session.add(lead)
    session.flush()
    payload = campaign_payload(offer, template, [lead.id])
    campaign = client.post("/api/v1/campaigns", json=payload).json()
    changed = dict(payload)
    changed["name"] = "Renamed synthetic campaign"

    response = client.patch(f"/api/v1/campaigns/{campaign['id']}", json=changed)

    assert response.status_code == 200, response.text
    assert response.json()["selected_lead_ids"] == [str(lead.id)]
    assert response.json()["selected_count"] == 1


def test_catalogue_drift_requires_a_new_campaign(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(business_name="Synthetic Drift Pharmacy")
    add_policy_provenance(lead)
    session.add(lead)
    session.flush()
    payload = campaign_payload(offer, template, [lead.id])
    campaign = client.post("/api/v1/campaigns", json=payload).json()

    template.body = "Changed after campaign creation. {{business_name}} {{opt_out}}"
    session.flush()

    generated = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert generated.status_code == 409
    assert "changed" in generated.json()["detail"].lower()
    current = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert current["status"] == "draft"


def test_suppression_after_preview_becomes_a_generation_skip(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(business_name="Synthetic Restricted Pharmacy")
    add_policy_provenance(lead)
    session.add(lead)
    session.flush()
    payload = campaign_payload(offer, template, [lead.id])
    preview = client.post("/api/v1/campaigns/preview", json=payload)
    assert preview.json()["eligible_count"] == 1
    campaign = client.post("/api/v1/campaigns", json=payload).json()

    suppression = client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "sms",
            "reason": "opt_out",
            "source": "Synthetic SMS reply",
            "note": "Stop SMS outreach.",
        },
    )
    assert suppression.status_code == 200

    generated = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert generated.status_code == 200
    assert generated.json()["draft_count"] == 0
    assert generated.json()["skip_count"] == 1
    assert generated.json()["skips"][0]["label"] == "Opted out or restricted"


def test_campaign_validation_rejects_duplicate_or_excess_ids(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead()
    session.add(lead)
    session.flush()

    duplicate = campaign_payload(offer, template, [lead.id, lead.id])
    assert client.post("/api/v1/campaigns/preview", json=duplicate).status_code == 422

    excessive = campaign_payload(
        offer, template, [uuid.uuid4() for _ in range(201)]
    )
    assert client.post("/api/v1/campaigns/preview", json=excessive).status_code == 422


def test_unknown_selected_lead_returns_not_found(
    client: TestClient, session: Session
) -> None:
    offer, template = campaign_catalogue(session)
    payload = campaign_payload(offer, template, [uuid.uuid4()])

    response = client.post("/api/v1/campaigns/preview", json=payload)

    assert response.status_code == 404, response.text
    assert "no longer exist" in response.json()["detail"]


def test_terminal_suppression_wins_over_landline_reason(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(
        business_name="Synthetic Restricted Landline",
        phone="+254202123456",
        whatsapp_capable=False,
    )
    add_policy_provenance(lead)
    session.add(lead)
    session.flush()

    suppression = client.post(
        f"/api/v1/leads/{lead.id}/suppressions",
        json={
            "scope": "sms",
            "reason": "opt_out",
            "source": "Synthetic SMS reply",
            "note": "Stop SMS outreach.",
        },
    )
    assert suppression.status_code == 200

    preview = client.post(
        "/api/v1/campaigns/preview",
        json=campaign_payload(offer, template, [lead.id]),
    )

    assert preview.status_code == 200
    assert preview.json()["skipped"][0]["label"] == "Opted out or restricted"


def test_generated_drafts_ignore_later_catalogue_changes(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(business_name="Synthetic Snapshot Pharmacy")
    add_policy_provenance(lead)
    session.add(lead)
    session.flush()
    campaign = client.post(
        "/api/v1/campaigns",
        json=campaign_payload(offer, template, [lead.id]),
    ).json()
    generated = client.post(f"/api/v1/campaigns/{campaign['id']}/generate")
    assert generated.status_code == 200, generated.text
    original = generated.json()["drafts"][0]

    template.body = "Changed template used {{business_name}}. {{opt_out}}"
    offer.price_min = 50000
    offer.price_max = 55000
    session.flush()

    current = client.get(f"/api/v1/campaigns/{campaign['id']}")
    assert current.status_code == 200
    snapshot = current.json()["drafts"][0]
    assert snapshot["rendered_body"] == original["rendered_body"]
    assert snapshot["template_snapshot"] == original["template_snapshot"]
    assert snapshot["offer_snapshot"] == original["offer_snapshot"]
    assert snapshot["eligibility_snapshot"] == original["eligibility_snapshot"]


def test_campaign_requires_active_matching_catalogue_records(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead()
    session.add(lead)
    session.flush()
    payload = campaign_payload(offer, template, [lead.id])

    template.is_active = False
    session.flush()
    inactive_template = client.post("/api/v1/campaigns/preview", json=payload)

    template.is_active = True
    template.channel = TemplateChannel.EMAIL
    session.flush()
    mismatched_channel = client.post("/api/v1/campaigns/preview", json=payload)

    assert inactive_template.status_code == 422
    assert mismatched_channel.status_code == 422


def test_only_creator_or_admin_can_mutate_a_campaign(
    client: TestClient, session: Session, make_lead
) -> None:
    offer, template = campaign_catalogue(session)
    lead = make_lead(business_name="Synthetic Permission Pharmacy")
    add_policy_provenance(lead)
    owner = User(
        email="campaign-owner@example.test",
        password_hash="not-used-in-request",
        role=UserRole.SALES,
        is_active=True,
        must_change_password=False,
    )
    other_seller = User(
        email="other-seller@example.test",
        password_hash="not-used-in-request",
        role=UserRole.SALES,
        is_active=True,
        must_change_password=False,
    )
    session.add_all([lead, owner, other_seller])
    session.flush()
    payload = campaign_payload(offer, template, [lead.id])

    app.dependency_overrides[get_current_user] = lambda: owner
    campaign = client.post("/api/v1/campaigns", json=payload).json()

    app.dependency_overrides[get_current_user] = lambda: other_seller
    update = client.patch(f"/api/v1/campaigns/{campaign['id']}", json=payload)
    archive = client.post(f"/api/v1/campaigns/{campaign['id']}/archive")

    assert update.status_code == 403
    assert archive.status_code == 403
    assert client.get(f"/api/v1/campaigns/{campaign['id']}").status_code == 200


def test_campaign_api_exposes_no_approval_or_delivery_path() -> None:
    campaign_paths = [
        path for path in app.openapi()["paths"] if path.startswith("/api/v1/campaigns")
    ]

    assert campaign_paths
    assert not any(
        forbidden in path
        for path in campaign_paths
        for forbidden in ("approve", "send", "fikatu", "schedule")
    )


def test_generation_rolls_back_without_partial_drafts(
    client: TestClient,
    session: Session,
    make_lead,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    offer, template = campaign_catalogue(session, body="Hi {{business_name}}")
    first = make_lead(business_name="Synthetic Rollback One")
    second = make_lead(business_name="Synthetic Rollback Two")
    add_policy_provenance(first)
    add_policy_provenance(second)
    session.add_all([first, second])
    session.flush()
    campaign = client.post(
        "/api/v1/campaigns",
        json=campaign_payload(offer, template, [first.id, second.id]),
    ).json()

    from app.services.draft_renderer import render_draft as real_render_draft

    calls = 0

    def fail_on_second_render(*args: object) -> tuple[None, object]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Synthetic generation failure")
        return real_render_draft(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(
        "app.services.campaign_service.render_draft",
        fail_on_second_render,
    )

    with pytest.raises(RuntimeError, match="Synthetic generation failure"):
        client.post(f"/api/v1/campaigns/{campaign['id']}/generate")

    current = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert current["status"] == "draft"
    assert current["draft_count"] == 0
    assert current["skip_count"] == 0
    assert current["drafts"] == []
