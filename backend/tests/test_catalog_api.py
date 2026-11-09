import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_session
from app.main import app
from app.models import MessageTemplate, Offer, TemplateChannel, User, UserRole


@pytest.fixture
def sales_client(session: Session) -> Iterator[TestClient]:
    seller = User(
        email="catalog-seller@example.test",
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


def create_offer(client: TestClient, **overrides: object):
    payload = {
        "name": "Starter Website",
        "slug": "starter-website",
        "description": "A focused first website.",
        "price_min": "40000.00",
        "price_max": "40000.00",
        "currency": "KES",
        "pitch_angle": "Get online without losing the personal service.",
        **overrides,
    }
    return client.post("/api/v1/offers", json=payload)


def test_admin_creates_multi_currency_offer(client: TestClient) -> None:
    response = create_offer(client, currency="USD")

    assert response.status_code == 201
    body = response.json()
    assert body["slug"] == "starter-website"
    assert body["currency"] == "USD"
    assert body["price_min"] == "40000.00"
    assert body["is_active"] is True


def test_catalog_endpoints_require_authentication(anonymous_client: TestClient) -> None:
    assert anonymous_client.get("/api/v1/offers").status_code == 401
    assert anonymous_client.get("/api/v1/templates").status_code == 401


def test_sales_can_read_but_not_write(
    client: TestClient, session: Session, sales_client: TestClient
) -> None:
    offer = Offer(name="Starter Website", slug="starter-website")
    session.add(offer)
    session.commit()

    assert sales_client.get("/api/v1/offers").status_code == 200
    forbidden = sales_client.post(
        "/api/v1/offers",
        json={"name": "Blocked", "slug": "blocked", "currency": "KES"},
    )
    assert forbidden.status_code == 403
    forbidden_template = sales_client.post(
        "/api/v1/templates",
        json={
            "offer_id": str(offer.id),
            "channel": "sms",
            "name": "Blocked",
            "variant": "A",
            "body": "Hi {{business_name}} {{opt_out}}",
            "variables": ["business_name", "opt_out"],
            "is_active": True,
        },
    )
    assert forbidden_template.status_code == 403
    template = MessageTemplate(
        offer=offer,
        channel=TemplateChannel.SMS,
        name="Review template",
        variant="A",
        body="Hi {{business_name}} {{opt_out}}",
        variables=["business_name", "opt_out"],
    )
    session.add(template)
    session.commit()
    assert (
        sales_client.patch(
            f"/api/v1/templates/{template.id}", json={"is_active": False}
        ).status_code
        == 403
    )
    assert (
        sales_client.patch(
            f"/api/v1/offers/{offer.id}", json={"is_active": False}
        ).status_code
        == 403
    )


def test_sales_only_sees_active_records(
    session: Session, sales_client: TestClient
) -> None:
    session.add_all(
        [
            Offer(name="Active", slug="active-offer"),
            Offer(name="Inactive", slug="inactive-offer", is_active=False),
        ]
    )
    session.commit()

    sales_offers = sales_client.get("/api/v1/offers").json()

    assert {row["slug"] for row in sales_offers} == {"active-offer"}


def test_sales_do_not_see_templates_for_inactive_offers(
    session: Session, sales_client: TestClient
) -> None:
    offer = Offer(name="Inactive offer", slug="inactive-offer", is_active=False)
    session.add(offer)
    session.flush()
    session.add(
        MessageTemplate(
            offer=offer,
            channel=TemplateChannel.SMS,
            name="Active orphan",
            variant="A",
            body="Hi {{business_name}} {{opt_out}}",
            variables=["business_name", "opt_out"],
        )
    )
    session.commit()

    assert sales_client.get("/api/v1/templates").json() == []


def test_admin_can_list_inactive_records(client: TestClient) -> None:
    assert create_offer(client, name="Active", slug="active-offer").status_code == 201
    assert (
        create_offer(
            client, name="Inactive", slug="inactive-offer", is_active=False
        ).status_code
        == 201
    )

    admin_offers = client.get("/api/v1/offers?include_inactive=true").json()
    assert {row["slug"] for row in admin_offers} == {"active-offer", "inactive-offer"}


def test_duplicate_slug_is_conflict(client: TestClient) -> None:
    assert create_offer(client).status_code == 201
    duplicate = create_offer(client, name="Another starter")

    assert duplicate.status_code == 409
    assert "slug" in duplicate.json()["detail"].lower()


def test_offer_deactivation_uses_patch(client: TestClient) -> None:
    offer = create_offer(client).json()
    response = client.patch(
        f"/api/v1/offers/{offer['id']}", json={"is_active": False}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert client.delete(f"/api/v1/offers/{offer['id']}").status_code == 405


def test_template_requires_known_variables_and_opt_out(client: TestClient) -> None:
    offer = create_offer(client).json()
    base = {
        "offer_id": offer["id"],
        "channel": "sms",
        "name": "No website A",
        "variant": "A",
        "body": "Hi {{business_name}}. {{opt_out}}",
        "variables": ["business_name", "opt_out"],
        "is_active": True,
    }

    created = client.post("/api/v1/templates", json=base)
    assert created.status_code == 201
    assert created.json()["variables"] == ["business_name", "opt_out"]

    unknown = client.post(
        "/api/v1/templates",
        json={
            **base,
            "name": "Unknown",
            "variant": "B",
            "body": "Hi {{secret_field}}. {{opt_out}}",
            "variables": ["secret_field", "opt_out"],
        },
    )
    assert unknown.status_code == 422
    assert "secret_field" in unknown.json()["detail"]

    missing_opt_out = client.post(
        "/api/v1/templates",
        json={
            **base,
            "name": "No opt out",
            "variant": "C",
            "body": "Hi {{business_name}}.",
            "variables": ["business_name"],
        },
    )
    assert missing_opt_out.status_code == 422
    assert "opt_out" in missing_opt_out.json()["detail"]


@pytest.mark.parametrize(
    "raw_contact",
    [
        "Call 0712 345678.",
        "Email owner@example.test.",
        "Reach us on +254 712 345678.",
    ],
)
def test_template_rejects_raw_contact_details(
    client: TestClient, raw_contact: str
) -> None:
    offer = create_offer(client).json()

    response = client.post(
        "/api/v1/templates",
        json={
            "offer_id": offer["id"],
            "channel": "sms",
            "name": "Unsafe contact",
            "variant": "A",
            "body": f"Hi {{{{business_name}}}}. {raw_contact} {{{{opt_out}}}}",
            "variables": ["business_name", "opt_out"],
        },
    )

    assert response.status_code == 422
    assert "contact details" in response.json()["detail"].lower()


def test_template_filtering_and_unknown_offer(client: TestClient) -> None:
    offer = create_offer(client).json()
    assert (
        client.post(
            "/api/v1/templates",
            json={
                "offer_id": offer["id"],
                "channel": "email",
                "name": "Email A",
                "variant": "A",
                "body": "Hello {{business_name}}. {{opt_out}}",
                "variables": ["business_name", "opt_out"],
            },
        ).status_code
        == 201
    )

    rows = client.get(
        f"/api/v1/templates?offer_id={offer['id']}&channel=email"
    ).json()
    assert len(rows) == 1
    assert rows[0]["channel"] == "email"

    unknown = client.get(f"/api/v1/templates?offer_id={uuid.uuid4()}")
    assert unknown.status_code == 404


def test_admin_can_update_and_deactivate_template(client: TestClient) -> None:
    offer = create_offer(client).json()
    template = client.post(
        "/api/v1/templates",
        json={
            "offer_id": offer["id"],
            "channel": "email",
            "name": "Email A",
            "variant": "A",
            "body": "Hello {{business_name}}. {{opt_out}}",
            "variables": ["business_name", "opt_out"],
        },
    ).json()

    updated = client.patch(
        f"/api/v1/templates/{template['id']}",
        json={
            "name": "Email A revised",
            "body": "Hello {{business_name}} from {{area}}. {{opt_out}}",
            "variables": ["area", "business_name", "opt_out"],
            "is_active": False,
        },
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Email A revised"
    assert updated.json()["variables"] == ["area", "business_name", "opt_out"]
    assert updated.json()["is_active"] is False
