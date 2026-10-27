"""Sign in, sign out, the current user, and changing your own password."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_session
from app.models import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserRead
from app.security import burn_password_check, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# One message for a wrong password, an unknown email, and a disabled account:
# the caller learns nothing about which accounts exist.
_INVALID_CREDENTIALS = "Invalid email or password."
_CHALLENGE = {"WWW-Authenticate": "Bearer"}


@router.post("/login", response_model=TokenResponse, summary="Sign in")
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.scalar(select(User).where(User.email == payload.email))

    if user is None:
        burn_password_check(payload.password)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_CREDENTIALS,
            headers=_CHALLENGE,
        )

    if not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_CREDENTIALS,
            headers=_CHALLENGE,
        )

    return TokenResponse(
        access_token=create_access_token(user),
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead, summary="The signed-in user")
def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out and invalidate issued tokens",
)
def logout(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    # Bumping the version invalidates every token minted before this call,
    # including this one. The client also drops the token it holds.
    user.token_version += 1
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/change-password",
    response_model=TokenResponse,
    summary="Change your own password",
)
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TokenResponse:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current password is incorrect.",
        )
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose a password you have not used here before.",
        )

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    # Invalidate the old token, then hand back one issued against the new version.
    user.token_version += 1
    session.commit()
    session.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user),
        user=UserRead.model_validate(user),
    )
