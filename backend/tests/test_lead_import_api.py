"""The import endpoint, through the real app against a real database.

The rules behind it are tested directly in `test_lead_import.py`; this file is
about the seam — the upload, the report, the download and the ways a request can
be refused before a row is ever read.

The fixtures are synthetic — reserved `+2547000...` numbers and invented names.
No test reads `data/`: that directory is gitignored, so such a test would pass
here and fail everywhere else (see `tests/fixtures/README.md`).
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.services.lead_import import MAX_UPLOAD_BYTES

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPORT_FIELDS = {
    "filename",
    "batch_id",
    "row_count",
    "accepted",
    "rejected",
    "duplicates",
    "requiring_review",
    "rejected_rows",
    "warnings",
}


def upload(client: TestClient, fixture: str, **params: str):
    content = (FIXTURES / fixture).read_bytes()
    return client.post(
        "/api/v1/leads/import",
        files={"file": (fixture, content, "text/csv")},
        params=params,
    )


def test_the_report_has_exactly_the_documented_shape(client: TestClient) -> None:
    response = upload(client, "import_clean.csv")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == REPORT_FIELDS
    assert body["filename"] == "import_clean.csv"
    assert (body["row_count"], body["accepted"], body["rejected"]) == (3, 3, 0)
    assert body["duplicates"] == 0
    assert body["requiring_review"] == 3
    assert body["batch_id"]
    assert body["rejected_rows"] == []
    assert body["warnings"] == []
    assert client.get("/api/v1/leads").json()["total"] == 3


def test_the_refused_rows_are_shaped_for_a_screen(client: TestClient) -> None:
    body = upload(client, "import_mixed.csv").json()

    assert body["duplicates"] == 1
    assert body["requiring_review"] == 3
    assert set(body["rejected_rows"][0]) == {"row", "business_name", "code", "reason"}
    assert set(body["warnings"][0]) == {"row", "field", "value", "code", "message"}
    assert body["rejected_rows"][0]["business_name"] == ""


def test_no_phone_number_appears_anywhere_in_the_report(client: TestClient) -> None:
    """The report is meant to be safe to paste into a chat."""
    body = json.dumps(upload(client, "import_mixed.csv").json())

    for digits in ("700000301", "700000302", "700000303", "700000307", "200000303"):
        assert digits not in body


def test_the_imported_leads_are_readable_with_their_timeline(client: TestClient) -> None:
    upload(client, "import_clean.csv")
    first = client.get("/api/v1/leads").json()["items"][0]

    detail = client.get(f"/api/v1/leads/{first['id']}").json()

    assert detail["business_name"] == "Synthetic Opticians One"
    assert [entry["type"] for entry in detail["activity"]] == ["lead.created", "lead.researched"]


def test_the_refused_rows_come_back_as_a_csv_download(client: TestClient) -> None:
    response = upload(client, "import_mixed.csv", format="csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="rejected-rows.csv"' in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert lines[0] == "row,business_name,code,reason"
    assert len(lines) == 5
    assert lines[1].startswith("3,")


def test_a_file_that_is_not_utf8_is_a_400(client: TestClient) -> None:
    response = upload(client, "import_not_utf8.csv")

    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_a_header_missing_a_column_we_read_is_a_400(client: TestClient) -> None:
    response = upload(client, "import_missing_column.csv")

    assert response.status_code == 400
    assert "Source" in response.json()["detail"]


def test_a_file_over_the_cap_is_a_413(client: TestClient) -> None:
    oversized = {"file": ("huge.csv", b"x" * (MAX_UPLOAD_BYTES + 1), "text/csv")}

    response = client.post("/api/v1/leads/import", files=oversized)

    assert response.status_code == 413
    assert "5 MB" in response.json()["detail"]


def test_a_header_only_file_answers_200_with_zeros(client: TestClient) -> None:
    response = upload(client, "import_header_only.csv")

    assert response.status_code == 200
    assert response.json()["row_count"] == 0


def test_the_endpoint_needs_a_file(client: TestClient) -> None:
    assert client.post("/api/v1/leads/import").status_code == 422
