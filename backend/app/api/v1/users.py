"""Administrator-only user listing for Sprint 3."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_session
from app.models import User
from app.schemas.auth import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="List application users (administrator only)",
)
def list_users(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[UserRead]:
    users = session.scalars(select(User).order_by(User.email)).all()
    return [UserRead.model_validate(user) for user in users]
