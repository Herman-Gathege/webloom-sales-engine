"""Lead routes. Parse, authorise (later), delegate — no business rules here."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.repositories import LeadRepository
from app.schemas import LeadDetailRead, LeadListRead, LeadRead
from app.services import LeadNotFoundError, LeadService
from app.services.lead_service import DEFAULT_LIMIT

router = APIRouter(prefix="/leads", tags=["leads"])


def get_lead_service(session: Session = Depends(get_session)) -> LeadService:
    return LeadService(LeadRepository(session))


@router.get("", response_model=LeadListRead, summary="List leads, newest first")
def list_leads(
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        description="Page size. Values above 200 are capped at 200.",
    ),
    offset: int = Query(0, ge=0, description="Rows to skip, for paging."),
    service: LeadService = Depends(get_lead_service),
) -> LeadListRead:
    page = service.list_leads(limit=limit, offset=offset)
    return LeadListRead(
        items=[LeadRead.model_validate(lead) for lead in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{lead_id}", response_model=LeadDetailRead, summary="One lead with its activity")
def get_lead(
    lead_id: str,
    service: LeadService = Depends(get_lead_service),
) -> LeadDetailRead:
    # lead_id is a string on purpose: a malformed id has to answer 404, and
    # declaring it as a uuid would make FastAPI answer 422 instead.
    try:
        lead = service.get_lead(lead_id)
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        ) from None
    return LeadDetailRead.model_validate(lead)
