"""Application users and the two roles Sprint 3 defines."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base


class UserRole(str, enum.Enum):
    """Deliberately small: an administrator and a seller."""

    ADMIN = "admin"
    SALES = "sales"


# varchar + check constraint rather than a native Postgres enum, matching how
# LeadStatus is stored: adding a role later is an ordinary migration.
user_role_type = Enum(
    UserRole,
    name="user_role",
    native_enum=False,
    length=16,
    validate_strings=True,
    create_constraint=True,
    values_callable=lambda roles: [role.value for role in roles],
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    # Stored lowercased; the API normalises before both create and lookup, so
    # "Anne@Example.com" and "anne@example.com" are one account.
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        user_role_type,
        nullable=False,
        default=UserRole.SALES,
        server_default=UserRole.SALES.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    # Bootstrap accounts start true; the frontend blocks the app until changed.
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    # Bumped on logout and on password change. Every token carries the version
    # it was issued with, so older tokens stop validating.
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("email <> ''", name="email_not_blank"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.email} {self.role.value}>"
