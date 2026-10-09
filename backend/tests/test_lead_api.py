"""The two Lead endpoints, through the real app and real rows."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Activity

LEAD_FIELDS = {
    "id",
    "business_name",
    "sector",
    "area",
    "phone",
    "whatsapp_capable",
    "website_status",
    "has_website",
    "source",
    "status",
    "created_at",
    "updated_at",
}


def test_health_answers_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_returns_exactly_the_contract_shape(
    client: TestClient, session: Session, make_lead
) -> None:
    session.add(make_lead(business_name="Mwangaza Opticians"))
    session.flush()

    response = client.get("/api/v1/leads")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert body["total"] == 1
    assert set(body["items"][0]) == LEAD_FIELDS
    assert body["items"][0]["business_name"] == "Mwangaza Opticians"


def test_list_defaults_to_limit_50(client: TestClient) -> None:
    body = client.get("/api/v1/leads").json()

    assert body["limit"] == 50
    assert body["offset"] == 0


def test_list_caps_the_limit_at_200(client: TestClient, session: Session, make_lead) -> None:
    for _ in range(3):
        session.add(make_lead())
    session.flush()

    body = client.get("/api/v1/leads", params={"limit": 500}).json()

    assert body["limit"] == 200
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_list_orders_newest_first(client: TestClient, session: Session, make_lead) -> None:
    started = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
    for index in range(3):
        session.add(
            make_lead(
                business_name=f"Business {index}",
                created_at=started + timedelta(minutes=index),
                updated_at=started + timedelta(minutes=index),
            )
        )
    session.flush()

    items = client.get("/api/v1/leads").json()["items"]

    assert [item["business_name"] for item in items] == [
        "Business 2",
        "Business 1",
        "Business 0",
    ]


def test_list_order_is_stable_when_created_at_ties(
    client: TestClient, session: Session, make_lead
) -> None:
    same_moment = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
    for index in range(4):
        session.add(make_lead(created_at=same_moment, updated_at=same_moment, area=f"Area {index}"))
    session.flush()

    first = [item["id"] for item in client.get("/api/v1/leads").json()["items"]]
    second = [item["id"] for item in client.get("/api/v1/leads").json()["items"]]

    assert first == second
    assert len(set(first)) == 4


def test_total_counts_before_pagination(client: TestClient, session: Session, make_lead) -> None:
    for index in range(3):
        session.add(make_lead(business_name=f"Business {index}"))
    session.flush()

    body = client.get("/api/v1/leads", params={"limit": 2}).json()

    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_offset_pages_without_repeating_or_skipping(
    client: TestClient, session: Session, make_lead
) -> None:
    started = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
    for index in range(3):
        session.add(
            make_lead(
                business_name=f"Business {index}",
                created_at=started + timedelta(minutes=index),
                updated_at=started + timedelta(minutes=index),
            )
        )
    session.flush()

    first_page = client.get("/api/v1/leads", params={"limit": 2, "offset": 0}).json()
    second_page = client.get("/api/v1/leads", params={"limit": 2, "offset": 2}).json()

    first_ids = [item["id"] for item in first_page["items"]]
    second_ids = [item["id"] for item in second_page["items"]]
    assert first_ids == [item["id"] for item in client.get("/api/v1/leads").json()["items"]][:2]
    assert set(first_ids).isdisjoint(second_ids)
    assert len(first_ids) + len(second_ids) == 3
    assert second_page["total"] == 3


def test_offset_past_the_end_returns_an_empty_page(
    client: TestClient, session: Session, make_lead
) -> None:
    session.add(make_lead())
    session.flush()

    body = client.get("/api/v1/leads", params={"offset": 25}).json()

    assert body["items"] == []
    assert body["total"] == 1
    assert body["offset"] == 25


def test_invalid_parameters_are_rejected(client: TestClient) -> None:
    for params in ({"limit": 0}, {"limit": -1}, {"offset": -1}):
        response = client.get("/api/v1/leads", params=params)
        assert response.status_code == 422, params
        assert "detail" in response.json()


def test_detail_returns_every_lead_field_plus_activity(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead(business_name="Baraka Chemist", phone="+254700111222", has_website=True)
    started = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
    lead.activity.append(
        Activity(
            type="lead.created",
            actor="system",
            summary="Imported from the Google Maps list",
            created_at=started,
        )
    )
    lead.activity.append(
        Activity(
            type="lead.researched",
            actor="system",
            summary="Website research recorded: has a website",
            created_at=started + timedelta(minutes=5),
        )
    )
    session.add(lead)
    session.flush()

    response = client.get(f"/api/v1/leads/{lead.id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == LEAD_FIELDS | {"activity"}
    assert body["business_name"] == "Baraka Chemist"
    assert body["has_website"] is True
    assert [entry["type"] for entry in body["activity"]] == ["lead.created", "lead.researched"]
    assert set(body["activity"][0]) == {
        "id",
        "lead_id",
        "type",
        "actor",
        "summary",
        "created_at",
    }
    assert body["activity"][0]["lead_id"] == str(lead.id)


def test_detail_activity_is_empty_never_null(
    client: TestClient, session: Session, make_lead
) -> None:
    lead = make_lead()
    session.add(lead)
    session.flush()

    body = client.get(f"/api/v1/leads/{lead.id}").json()

    assert body["activity"] == []


def test_detail_only_returns_that_lead_s_activity(
    client: TestClient, session: Session, make_lead
) -> None:
    wanted = make_lead()
    other = make_lead()
    wanted.activity.append(Activity(type="lead.created", actor="system", summary="Wanted"))
    other.activity.append(Activity(type="lead.created", actor="system", summary="Other"))
    session.add_all([wanted, other])
    session.flush()

    body = client.get(f"/api/v1/leads/{wanted.id}").json()

    assert [entry["summary"] for entry in body["activity"]] == ["Wanted"]


def test_unknown_lead_is_a_404_with_the_contract_body(client: TestClient) -> None:
    response = client.get(f"/api/v1/leads/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Lead not found"}


def test_malformed_id_is_a_404_not_a_500(client: TestClient) -> None:
    response = client.get("/api/v1/leads/not-a-uuid")

    assert response.status_code == 404
    assert response.json() == {"detail": "Lead not found"}


def test_timestamps_are_iso_8601_utc(client: TestClient, session: Session, make_lead) -> None:
    session.add(make_lead())
    session.flush()

    item = client.get("/api/v1/leads").json()["items"][0]

    for field in ("created_at", "updated_at"):
        assert item[field].endswith("Z"), item[field]
        parsed = datetime.fromisoformat(item[field])
        assert parsed.tzinfo == UTC
