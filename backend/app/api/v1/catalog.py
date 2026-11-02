"""Offer and Sales Engine template endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_admin, require_password_current
from app.database import get_session
from app.models import TemplateChannel, User
from app.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import (
    OfferCreate,
    OfferRead,
    OfferUpdate,
    TemplateCreate,
    TemplateRead,
    TemplateUpdate,
)
from app.services.catalog_service import (
    CatalogConflictError,
    CatalogNotFoundError,
    CatalogService,
    CatalogValidationError,
)

router = APIRouter(tags=["catalog"])


def get_service(session: Session = Depends(get_session)) -> CatalogService:
    return CatalogService(CatalogRepository(session))


def _translate(error: Exception) -> HTTPException:
    if isinstance(error, CatalogNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, CatalogConflictError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


@router.get("/offers", response_model=list[OfferRead])
def list_offers(
    include_inactive: bool = Query(False),
    user: User = Depends(require_password_current),
    service: CatalogService = Depends(get_service),
):
    if include_inactive and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return service.list_offers(include_inactive=include_inactive)


@router.post("/offers", response_model=OfferRead, status_code=status.HTTP_201_CREATED)
def create_offer(
    payload: OfferCreate,
    _: User = Depends(require_admin),
    service: CatalogService = Depends(get_service),
):
    try:
        return service.create_offer(payload.model_dump())
    except (CatalogConflictError, CatalogValidationError) as exc:
        raise _translate(exc) from exc


@router.patch("/offers/{offer_id}", response_model=OfferRead)
def update_offer(
    offer_id: uuid.UUID,
    payload: OfferUpdate,
    _: User = Depends(require_admin),
    service: CatalogService = Depends(get_service),
):
    try:
        return service.update_offer(offer_id, payload.model_dump(exclude_unset=True))
    except (CatalogConflictError, CatalogNotFoundError, CatalogValidationError) as exc:
        raise _translate(exc) from exc


@router.get("/templates", response_model=list[TemplateRead])
def list_templates(
    offer_id: uuid.UUID | None = None,
    channel: TemplateChannel | None = None,
    include_inactive: bool = Query(False),
    user: User = Depends(require_password_current),
    service: CatalogService = Depends(get_service),
):
    if include_inactive and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    try:
        return service.list_templates(
            include_inactive=include_inactive,
            offer_id=offer_id,
            channel=channel,
        )
    except CatalogNotFoundError as exc:
        raise _translate(exc) from exc


@router.post(
    "/templates", response_model=TemplateRead, status_code=status.HTTP_201_CREATED
)
def create_template(
    payload: TemplateCreate,
    _: User = Depends(require_admin),
    service: CatalogService = Depends(get_service),
):
    try:
        return service.create_template(payload.model_dump())
    except (CatalogConflictError, CatalogNotFoundError, CatalogValidationError) as exc:
        raise _translate(exc) from exc


@router.patch("/templates/{template_id}", response_model=TemplateRead)
def update_template(
    template_id: uuid.UUID,
    payload: TemplateUpdate,
    _: User = Depends(require_admin),
    service: CatalogService = Depends(get_service),
):
    try:
        return service.update_template(template_id, payload.model_dump(exclude_unset=True))
    except (CatalogConflictError, CatalogNotFoundError, CatalogValidationError) as exc:
        raise _translate(exc) from exc
