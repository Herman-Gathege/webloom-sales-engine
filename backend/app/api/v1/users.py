"""Administrator-only user management (Sprint 5)."""

import secrets
import string
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_session
from app.models import User, UserRole
from app.schemas.auth import (
    TemporaryPasswordResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

_TEMP_ALPHABET = string.ascii_letters + string.digits


def _temp_password() -> str:
    return "".join(secrets.choice(_TEMP_ALPHABET) for _ in range(16))


def _active_admin_count(session: Session) -> int:
    return session.scalar(
        select(func.count()).select_from(User).where(
            User.role == UserRole.ADMIN, User.is_active.is_(True)
        )
    ) or 0


@router.get("", response_model=list[UserRead], summary="List application users")
def list_users(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[UserRead]:
    users = session.scalars(select(User).order_by(User.email)).all()
    return [UserRead.model_validate(user) for user in users]


@router.post(
    "",
    response_model=TemporaryPasswordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (administrator only)",
)
def create_user(
    payload: UserCreate,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> TemporaryPasswordResponse:
    existing = session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    temp = _temp_password()
    user = User(
        email=payload.email,
        password_hash=hash_password(temp),
        role=payload.role,
        is_active=True,
        must_change_password=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return TemporaryPasswordResponse(user=UserRead.model_validate(user), temporary_password=temp)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user (administrator only)",
)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UserRead:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.email is not None and payload.email != user.email:
        existing = session.scalar(select(User).where(User.email == payload.email))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        user.email = payload.email

    if payload.role is not None and payload.role != user.role:
        # last active admin protection for demotion
        if (
            user.role == UserRole.ADMIN
            and user.is_active
            and payload.role != UserRole.ADMIN
            and _active_admin_count(session) <= 1
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last active administrator",
            )
        user.role = payload.role

    if payload.is_active is not None and payload.is_active != user.is_active:
        if not payload.is_active:
            if (
                user.role == UserRole.ADMIN
                and user.is_active
                and _active_admin_count(session) <= 1
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active administrator",
                )
            user.is_active = False
        else:
            user.is_active = True

    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user)


@router.post(
    "/{user_id}/reset-password",
    response_model=TemporaryPasswordResponse,
    summary="Reset a user password (administrator only)",
)
def reset_password(
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> TemporaryPasswordResponse:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    temp = _temp_password()
    user.password_hash = hash_password(temp)
    user.must_change_password = True
    user.token_version += 1
    session.commit()
    session.refresh(user)
    return TemporaryPasswordResponse(user=UserRead.model_validate(user), temporary_password=temp)
