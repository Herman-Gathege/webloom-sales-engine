"""Manual lead creation reuses the lead, provenance and compliance conventions."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_session
from app.main import app
from app.models import Activity, Lead, User, UserRole


@pytest.fixture
def sales_client(session: Session) -> Iterator[TestClient]:
    seller = User(
        email="seller@example.test",
        password_hash="not-used",
        role=UserRole.SALES,
        is_active=True,
        must_change_password=False,
    )
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: seller
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def manual_lead(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "business_name": "Synthetic Wadi Bakery",
        "sector": "Bakeries",
        "area": "Westlands",
        "phone": "0712 345 678",
        "email": "HELLO@EXAMPLE.TEST",
        "whatsapp_capable": True,
        "website_status": "Website not checked",
        "has_website": False,
        "source": "Manual entry",
        "source_name": "Manual seller entry",
        "source_url": "https://example.test/synthetic-source",
        "collection_date": "2026-11-09",
        "collection_method": "Seller-entered test record",
        "intended_purpose": "Business outreach",
        "contact_type": "generic_business",
        "contact_name": "Synthetic Owner",
    }
    payload.update(overrides)
    return payload


def test_admin_creates_one_lead_with_provenance_compliance_and_audit(
    client: TestClient, session: Session
) -> None:
    response = client.post("/api/v1/leads", json=manual_lead())

    assert response.status_code == 201
    body = response.json()
    assert body["business_name"] == "Synthetic Wadi Bakery"
    assert body["phone"] == "+254712345678"
    assert body["email"] == "hello@example.test"
    assert body["source"] == "manual_entry"
    assert body["has_website"] is False
    assert body["provenance"]["source_name"] == "Manual seller entry"
    assert body["provenance"]["collection_method"] == "Seller-entered test record"
    assert body["provenance"]["contact_type"] == "generic_business"
    assert {row["channel"] for row in body["eligibility"]} == {
        "email",
        "sms",
        "whatsapp",
    }
    assert all(row["state"] == "needs_review" for row in body["eligibility"])
    assert body["compliance"]["status"] in {"eligible", "needs_review"}
    assert [entry["type"] for entry in body["activity"][:2]] == [
        "lead.created",
        "lead.researched",
    ]
    assert body["activity"][0]["actor"] == "herman@example.test"
    assert body["activity"][0]["details"]["entry_method"] == "manual"
    activity_text = " ".join(
        f"{entry['summary']} {entry['details']}" for entry in body["activity"]
    )
    assert "+254712345678" not in activity_text
    assert "hello@example.test" not in activity_text
    assert session.scalar(select(func.count()).select_from(Lead)) == 1


def test_sales_user_can_create_a_lead(sales_client: TestClient) -> None:
    response = sales_client.post(
        "/api/v1/leads",
        json=manual_lead(business_name="Synthetic Seller Business"),
    )

    assert response.status_code == 201
    assert response.json()["business_name"] == "Synthetic Seller Business"


def test_an_email_only_lead_can_be_created(client: TestClient) -> None:
    response = client.post(
        "/api/v1/leads",
        json=manual_lead(
            business_name="Synthetic Email Only Business",
            phone=None,
            email="email-only@example.test",
            whatsapp_capable=False,
        ),
    )

    assert response.status_code == 201
    assert response.json()["phone"] is None
    assert response.json()["email"] == "email-only@example.test"


def test_create_requires_at_least_one_contact(client: TestClient) -> None:
    response = client.post(
        "/api/v1/leads",
        json=manual_lead(phone=None, email=None),
    )

    assert response.status_code == 422
    assert "phone number or email" in response.text.lower()


def test_create_rejects_an_unreadable_phone(client: TestClient) -> None:
    response = client.post(
        "/api/v1/leads",
        json=manual_lead(phone="call the owner"),
    )

    assert response.status_code == 422
    assert "phone" in response.json()["detail"].lower()


def test_create_refuses_a_duplicate_phone(client: TestClient) -> None:
    first = client.post("/api/v1/leads", json=manual_lead())
    duplicate = client.post(
        "/api/v1/leads",
        json=manual_lead(
            business_name="Different Synthetic Business",
            email="different@example.test",
            phone="+254 712 345 678",
        ),
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert "phone" in duplicate.json()["detail"].lower()


def test_create_refuses_the_same_business_and_email(client: TestClient) -> None:
    first = client.post("/api/v1/leads", json=manual_lead())
    duplicate = client.post(
        "/api/v1/leads",
        json=manual_lead(phone="+254700000199"),
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert "email" in duplicate.json()["detail"].lower()


def test_manual_creation_needs_a_source(client: TestClient) -> None:
    response = client.post("/api/v1/leads", json=manual_lead(source=""))

    assert response.status_code == 422
    assert "source" in response.text.lower()


def test_manual_creation_is_audited_without_contact_details(
    client: TestClient, session: Session
) -> None:
    response = client.post("/api/v1/leads", json=manual_lead())
    assert response.status_code == 201

    activities = session.scalars(select(Activity)).all()
    assert len(activities) >= 2
    serialised = " ".join(str(activity.details) for activity in activities)
    assert "254712345678" not in serialised
    assert "hello@example.test" not in serialised

