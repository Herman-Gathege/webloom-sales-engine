"""Password hashing and signed access tokens.

One module owns both so there is exactly one way to hash a password and one way
to mint or read a token. FikaTu uses the same pair of libraries (ADR-001).
"""

from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.models.user import User

_passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """The token is malformed, expired, or missing a required claim."""


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """A bcrypt hash used only to spend the same time on unknown emails.

    Hashing costs a few hundred milliseconds, so it is created once, lazily,
    rather than at import time where it would slow every test run.
    """
    return _passwords.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _passwords.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _passwords.verify(password, password_hash)
    except ValueError:
        # A corrupt or non-bcrypt hash is a failed login, never a 500.
        return False


def burn_password_check(password: str) -> None:
    """Do the work of a password check without revealing whether a user exists."""
    verify_password(password, _dummy_hash())


def create_access_token(user: User) -> str:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "ver": user.token_version,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise TokenError("Invalid or expired token.") from exc

    for claim in ("sub", "role", "ver", "exp"):
        if claim not in payload:
            raise TokenError("Token is missing a required claim.")
    return payload
