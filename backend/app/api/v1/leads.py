"""Lead routes. Parse, authorise, delegate — no business rules here.

Every route here sits behind `get_current_user` (attached to this router in
`router.py`). The routes that record compliance facts also take the user so the
actor is the signed-in person rather than a value the caller supplies.
"""

from typing import Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_session
from app.models import LeadStatus, User
from app.repositories import LeadRepository
from app.schemas import (
    EligibilityReviewRequest,
    ImportReviewRowRead,
    ImportSummary,
    LeadDetailRead,
    LeadFilterOptionsRead,
    LeadListRead,
    LeadRead,
    OutreachCheckRequest,
    OutreachCheckResponse,
    OutreachGateResultRead,
    RefusedRowRead,
    RowWarningRead,
    SuppressionCreate,
)
from app.services import (
    MAX_UPLOAD_BYTES,
    ComplianceService,
    ComplianceTargetError,
    EligibilityDecision,
    ImportFileError,
    LeadImportService,
    LeadNotFoundError,
    LeadService,
    OutreachGateService,
    SuppressionDecision,
    refused_rows_csv,
)
from app.services.lead_service import DEFAULT_LIMIT

router = APIRouter(prefix="/leads", tags=["leads"])


def get_lead_service(session: Session = Depends(get_session)) -> LeadService:
    return LeadService(LeadRepository(session))


def get_import_service(session: Session = Depends(get_session)) -> LeadImportService:
    return LeadImportService(LeadRepository(session))


def get_compliance_service(session: Session = Depends(get_session)) -> ComplianceService:
    return ComplianceService(LeadRepository(session))


def get_outreach_gate_service(
    session: Session = Depends(get_session),
) -> OutreachGateService:
    return OutreachGateService(LeadRepository(session))


@router.get("", response_model=LeadListRead, summary="List leads, newest first")
def list_leads(
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        description="Page size. Values above 200 are capped at 200.",
    ),
    offset: int = Query(0, ge=0, description="Rows to skip, for paging."),
    q: str | None = Query(
        None,
        max_length=255,
        description="Search business, phone, email, sector, area, or source.",
    ),
    sector: str | None = Query(None, max_length=255),
    area: str | None = Query(None, max_length=255),
    source: str | None = Query(None, max_length=64),
    website: Literal["yes", "no"] | None = Query(None),
    lead_status: LeadStatus | None = Query(None, alias="status"),
    compliance_status: Literal[
        "eligible", "needs_review", "blocked", "invalid"
    ] | None = Query(None),
    data_quality_status: Literal["complete", "incomplete", "invalid"] | None = Query(
        None
    ),
    provenance: Literal["available", "missing", "incomplete"] | None = Query(None),
    outreach_ready: bool | None = Query(None),
    has_suppression: bool | None = Query(None),
    batch_id: UUID | None = Query(None),
    sort: Literal[
        "newest", "oldest", "business_name", "compliance_status"
    ] = Query("newest"),
    service: LeadService = Depends(get_lead_service),
) -> LeadListRead:
    page = service.list_leads(
        limit=limit,
        offset=offset,
        q=q,
        sector=sector,
        area=area,
        source=source,
        website=website,
        status=lead_status,
        compliance_status=compliance_status,
        data_quality_status=data_quality_status,
        provenance=provenance,
        outreach_ready=outreach_ready,
        has_suppression=has_suppression,
        batch_id=batch_id,
        sort=sort,
    )
    return LeadListRead(
        items=[LeadRead.model_validate(lead) for lead in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post(
    "/import",
    response_model=ImportSummary,
    summary="Import a researched lead list from CSV",
    responses={
        200: {
            "description": (
                "What happened to every row. `format=csv` answers the refusals as a file."
            ),
            "content": {"text/csv": {"schema": {"type": "string"}}},
        },
        400: {"description": "The file is not UTF-8, or a column we read is missing."},
        413: {"description": "The file is larger than 5 MB."},
    },
)
def import_leads(
    file: UploadFile = File(..., description="The research list, as a UTF-8 CSV."),
    report_format: str = Query(
        "json",
        alias="format",
        pattern="^(json|csv)$",
        description="`json` for the summary, `csv` to download the refused rows.",
    ),
    current_user: User = Depends(get_current_user),
    service: LeadImportService = Depends(get_import_service),
) -> ImportSummary | Response:
    # Read one byte past the cap so an oversized upload is refused rather than
    # held in memory; Starlette has already spooled the rest to a temporary file.
    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"The file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        result = service.import_file(
            raw,
            file.filename or "upload.csv",
            imported_by=current_user.email,
        )
    except ImportFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from None

    if report_format == "csv":
        return Response(
            content=refused_rows_csv(result),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="rejected-rows.csv"',
            },
        )

    return ImportSummary(
        filename=result.filename,
        batch_id=result.batch_id,
        row_count=result.row_count,
        accepted=result.accepted,
        created=result.created,
        rejected=result.rejected,
        matched=result.matched,
        duplicates=result.duplicates,
        eligible=result.eligible,
        needs_review=result.needs_review,
        blocked=result.blocked,
        invalid=result.invalid,
        provenance_incomplete=result.provenance_incomplete,
        requiring_review=result.requiring_review,
        rejected_rows=[RefusedRowRead.model_validate(row) for row in result.refused],
        review_rows=[
            ImportReviewRowRead.model_validate(row) for row in result.review_rows
        ],
        warnings=[RowWarningRead.model_validate(warning) for warning in result.warnings],
    )


@router.get(
    "/filter-options",
    response_model=LeadFilterOptionsRead,
    summary="Values available to the Lead Desk filters",
)
def filter_options(
    service: LeadService = Depends(get_lead_service),
) -> LeadFilterOptionsRead:
    return LeadFilterOptionsRead.model_validate(service.filter_options())


@router.post(
    "/outreach-check",
    response_model=OutreachCheckResponse,
    summary="Recheck one or more leads at the outreach eligibility boundary",
)
def check_bulk_outreach(
    request: OutreachCheckRequest,
    current_user: User = Depends(get_current_user),
    service: OutreachGateService = Depends(get_outreach_gate_service),
) -> OutreachCheckResponse:
    try:
        results = service.check_many(
            request.lead_ids,
            request.channel,
            actor=current_user.email,
        )
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        ) from None
    return OutreachCheckResponse(
        channel=request.channel,
        results=[OutreachGateResultRead.model_validate(result) for result in results],
    )


@router.post(
    "/{lead_id}/outreach-check/{channel}",
    response_model=OutreachGateResultRead,
    summary="Recheck a lead immediately before an outreach action",
)
def check_outreach(
    lead_id: str,
    channel: str = Path(pattern="^(email|sms|whatsapp)$"),
    current_user: User = Depends(get_current_user),
    service: OutreachGateService = Depends(get_outreach_gate_service),
) -> OutreachGateResultRead:
    try:
        result = service.check(lead_id, channel, actor=current_user.email)
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        ) from None
    return OutreachGateResultRead.model_validate(result)


@router.put(
    "/{lead_id}/eligibility/{channel}",
    response_model=LeadDetailRead,
    summary="Record a human channel-eligibility review",
)
def review_eligibility(
    lead_id: str,
    decision: EligibilityReviewRequest,
    channel: str = Path(pattern="^(email|sms|whatsapp)$"),
    current_user: User = Depends(get_current_user),
    service: ComplianceService = Depends(get_compliance_service),
) -> LeadDetailRead:
    try:
        lead = service.review_eligibility(
            lead_id,
            channel,
            EligibilityDecision(
                state=decision.state,
                lawful_basis=decision.lawful_basis,
                evidence_summary=decision.evidence_summary,
                evidence_source=decision.evidence_source,
                intended_purpose=decision.intended_purpose,
                contact_context=decision.contact_context,
                # The reviewer is whoever is signed in; a request body cannot
                # claim to be someone else.
                reviewer=current_user.email,
                rationale=decision.rationale,
            ),
        )
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        ) from None
    except ComplianceTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from None
    return LeadDetailRead.model_validate(lead)


@router.post(
    "/{lead_id}/suppressions",
    response_model=LeadDetailRead,
    summary="Record a channel-specific or all-marketing opt-out",
)
def record_suppression(
    lead_id: str,
    request: SuppressionCreate,
    current_user: User = Depends(get_current_user),
    service: ComplianceService = Depends(get_compliance_service),
) -> LeadDetailRead:
    try:
        lead = service.record_suppression(
            lead_id,
            SuppressionDecision(
                scope=request.scope,
                reason=request.reason,
                source=request.source,
                recorded_by=current_user.email,
                note=request.note,
            ),
        )
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        ) from None
    except ComplianceTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from None
    return LeadDetailRead.model_validate(lead)


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
