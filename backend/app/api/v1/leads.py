"""Lead routes. Parse, authorise (later), delegate — no business rules here."""

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

from app.database import get_session
from app.repositories import LeadRepository
from app.schemas import (
    EligibilityReviewRequest,
    ImportSummary,
    LeadDetailRead,
    LeadListRead,
    LeadRead,
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
        result = service.import_file(raw, file.filename or "upload.csv")
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
        rejected=result.rejected,
        duplicates=result.duplicates,
        requiring_review=result.requiring_review,
        rejected_rows=[RefusedRowRead.model_validate(row) for row in result.refused],
        warnings=[RowWarningRead.model_validate(warning) for warning in result.warnings],
    )


@router.put(
    "/{lead_id}/eligibility/{channel}",
    response_model=LeadDetailRead,
    summary="Record a human channel-eligibility review",
)
def review_eligibility(
    lead_id: str,
    decision: EligibilityReviewRequest,
    channel: str = Path(pattern="^(email|sms|whatsapp)$"),
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
                reviewer=decision.reviewer,
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
    service: ComplianceService = Depends(get_compliance_service),
) -> LeadDetailRead:
    try:
        lead = service.record_suppression(
            lead_id,
            SuppressionDecision(
                scope=request.scope,
                reason=request.reason,
                source=request.source,
                recorded_by=request.recorded_by,
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
