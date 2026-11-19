"""Sprint 5 campaign preparation and draft generation."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_session
from app.models import User
from app.repositories import CampaignRepository, LeadRepository
from app.schemas.campaign import (
    CampaignDetailRead,
    CampaignInput,
    CampaignListRead,
    CampaignPreviewRead,
    CampaignUpdate,
)
from app.services.campaign_service import (
    CampaignConflictError,
    CampaignNotFoundError,
    CampaignPermissionError,
    CampaignService,
    CampaignValidationError,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def get_campaign_service(session: Session = Depends(get_session)) -> CampaignService:
    return CampaignService(
        CampaignRepository(session),
        LeadRepository(session),
    )


def _translate(error: Exception) -> HTTPException:
    if isinstance(error, CampaignNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, CampaignPermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, CampaignConflictError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


@router.get("", response_model=CampaignListRead)
def list_campaigns(
    include_archived: bool = Query(False),
    _: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignListRead:
    return service.list_campaigns(include_archived=include_archived)


@router.post("/preview", response_model=CampaignPreviewRead)
def preview_campaign(
    request: CampaignInput,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignPreviewRead:
    try:
        return service.preview(request, actor=current_user)
    except (
        CampaignNotFoundError,
        CampaignValidationError,
        CampaignConflictError,
    ) as exc:
        raise _translate(exc) from exc


@router.post(
    "",
    response_model=CampaignDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign(
    request: CampaignInput,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailRead:
    try:
        return service.create(request, actor=current_user)
    except (
        CampaignNotFoundError,
        CampaignValidationError,
        CampaignConflictError,
    ) as exc:
        raise _translate(exc) from exc


@router.get("/{campaign_id}", response_model=CampaignDetailRead)
def get_campaign(
    campaign_id: uuid.UUID,
    _: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailRead:
    try:
        return service.get_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        raise _translate(exc) from exc


@router.patch("/{campaign_id}", response_model=CampaignDetailRead)
def update_campaign(
    campaign_id: uuid.UUID,
    request: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailRead:
    try:
        return service.update(campaign_id, request, actor=current_user)
    except (
        CampaignNotFoundError,
        CampaignPermissionError,
        CampaignConflictError,
        CampaignValidationError,
    ) as exc:
        raise _translate(exc) from exc


@router.post("/{campaign_id}/generate", response_model=CampaignDetailRead)
def generate_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailRead:
    try:
        return service.generate(campaign_id, actor=current_user)
    except (
        CampaignNotFoundError,
        CampaignPermissionError,
        CampaignConflictError,
        CampaignValidationError,
    ) as exc:
        raise _translate(exc) from exc


@router.post("/{campaign_id}/archive", response_model=CampaignDetailRead)
def archive_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailRead:
    try:
        return service.archive(campaign_id, actor=current_user)
    except (CampaignNotFoundError, CampaignPermissionError) as exc:
        raise _translate(exc) from exc


@router.post("/{campaign_id}/restore", response_model=CampaignDetailRead)
def restore_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignDetailRead:
    try:
        return service.restore(campaign_id, actor=current_user)
    except (CampaignNotFoundError, CampaignPermissionError) as exc:
        raise _translate(exc) from exc
