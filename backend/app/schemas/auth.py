"""Request and response shapes for login, password changes, and users."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole
from app.schemas.types import UtcDatetime


def _normalise_email(value: str) -> str:
    email = value.strip().lower()
    local, _, domain = email.partition("@")
    if not local or not domain or "." not in domain or " " in email:
        raise ValueError("Enter a valid email address.")
    return email


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    # bcrypt ignores anything past 72 bytes, so longer input is refused rather
    # than silently truncated.
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return _normalise_email(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    must_change_password: bool
    created_at: UtcDatetime


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: UserRole = UserRole.SALES

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return _normalise_email(value)


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalise_email(value)


class TemporaryPasswordResponse(BaseModel):
    user: UserRead
    temporary_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def not_predictable(cls, value: str) -> str:
        if value.isdigit() or value.strip().lower() in {"password", "changeme", "qwertyui"}:
            raise ValueError("Choose a less predictable password.")
        return value
