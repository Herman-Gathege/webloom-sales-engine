"""Downloadable and campaign-readiness CSV fixtures stay importer-compatible."""

import csv
import io
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead
from app.repositories import LeadRepository
from app.services.lead_import import (
    COLUMNS_READ,
    IMPORT_TEMPLATE_ROWS,
    OPTIONAL_COLUMNS,
    LeadImportService,
)

CAMPAIGN_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "campaign_readiness.csv"


def test_downloadable_template_has_the_exact_importer_columns(client: TestClient) -> None:
    response = client.get("/api/v1/leads/import-template")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="wadi-lead-import-template.csv"' in response.headers[
        "content-disposition"
    ]
    reader = csv.DictReader(io.StringIO(response.text))
    assert reader.fieldnames == list(COLUMNS_READ + OPTIONAL_COLUMNS)
    assert len(list(reader)) == len(IMPORT_TEMPLATE_ROWS)


def test_downloaded_template_imports_without_column_renaming(client: TestClient) -> None:
    template = client.get("/api/v1/leads/import-template")

    imported = client.post(
        "/api/v1/leads/import",
        files={
            "file": (
                "wadi-lead-import-template.csv",
                template.content,
                "text/csv",
            )
        },
    )

    assert imported.status_code == 200
    body = imported.json()
    assert body["row_count"] == len(IMPORT_TEMPLATE_ROWS)
    assert body["accepted"] == len(IMPORT_TEMPLATE_ROWS)
    assert body["rejected"] == 0


def test_campaign_fixture_covers_contact_website_and_eligibility_variation(
    session: Session,
) -> None:
    result = LeadImportService(LeadRepository(session)).import_file(
        CAMPAIGN_FIXTURE.read_bytes(),
        CAMPAIGN_FIXTURE.name,
        imported_by="fixture-test@example.test",
    )

    assert (result.row_count, result.accepted, result.rejected) == (8, 8, 0)
    assert result.automated_eligible >= 4
    assert result.requiring_review >= 4
    leads = list(session.scalars(select(Lead)))
    assert any(lead.has_website for lead in leads)
    assert any(not lead.has_website for lead in leads)
    assert any(lead.phone and lead.phone.startswith("+2542") for lead in leads)
    assert any(lead.email for lead in leads)
    assert any(lead.email is None for lead in leads)
