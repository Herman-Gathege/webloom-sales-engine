"""Authentication dependencies: who is calling, and may they do this?

The API is the authority. The frontend hides what it likes; every protected
route still runs through `get_current_user`, and every admin route through
`require_admin`.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import User, UserRole
from app.security import TokenError, decode_access_token

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT from POST /api/v1/auth/login",
)

_CHALLENGE = {"WWW-Authenticate": "Bearer"}


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers=_CHALLENGE,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Resolve the bearer token to an active user, or raise 401.

    Also rejects tokens issued before the user's last logout or password
    change: the `ver` claim must match the user's current `token_version`.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload["sub"]))
    except (TokenError, ValueError):
        raise _unauthorized("Invalid or expired token") from None

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")
    if payload.get("ver") != user.token_version:
        raise _unauthorized("Session is no longer valid")

    return user


def require_password_current(user: User = Depends(get_current_user)) -> User:
    """Signed in, and past the forced first-login password change.

    The frontend sends these accounts to the change-password screen, but the
    API is what actually refuses to serve lead data until the password is set.
    """
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Set a new password before continuing",
        )
    return user


def require_admin(user: User = Depends(require_password_current)) -> User:
    """Authenticated, password-current, and an administrator."""
    if user.role is not UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user
