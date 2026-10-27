"""Create the team's development administrator accounts.

Run from `backend/`:  python -m app.bootstrap

Idempotent by design: an account that already exists is left exactly as it is,
including its password. That means rerunning this can never reset somebody's
password, and it is safe to run on every fresh checkout.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import User, UserRole
from app.security import hash_password

# Confirmed team accounts. All four are administrators for Sprint 3.
ADMIN_EMAILS: tuple[str, ...] = (
    "hermangathege@kbc.co.ke",
    "sharonkendi@kbc.co.ke",
    "annewaithaka68@gmail.com",
    "markmwenesi@kbc.co.ke",
)


def _create_accounts(
    session: Session, password: str, emails: tuple[str, ...] | list[str], role: UserRole
) -> tuple[int, int]:
    """Return (created, already_present). Never updates an existing account."""
    password_hash = hash_password(password)
    created = 0
    present = 0

    for email in emails:
        email = email.strip().lower()
        existing = session.scalar(select(User).where(User.email == email))
        if existing is not None:
            present += 1
            continue
        session.add(
            User(
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=True,
                must_change_password=True,
            )
        )
        created += 1

    session.commit()
    return created, present


def create_admins(session: Session, password: str) -> tuple[int, int]:
    return _create_accounts(session, password, ADMIN_EMAILS, UserRole.ADMIN)


def create_sales(session: Session, password: str, emails: list[str]) -> tuple[int, int]:
    return _create_accounts(session, password, emails, UserRole.SALES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create the development administrator accounts."
    )
    parser.add_argument(
        "--sales",
        action="append",
        default=[],
        metavar="EMAIL",
        help="Also create a sales account for this email (repeatable).",
    )
    args = parser.parse_args(argv)

    settings = get_settings()

    if settings.environment == "production":
        print(
            "Refusing to create bootstrap accounts with ENVIRONMENT=production.",
            file=sys.stderr,
        )
        return 1

    password = settings.bootstrap_admin_password
    if not password:
        print(
            "Set BOOTSTRAP_ADMIN_PASSWORD (at least 8 characters) before running this.",
            file=sys.stderr,
        )
        return 1
    if len(password) < 8:
        print("BOOTSTRAP_ADMIN_PASSWORD must be at least 8 characters.", file=sys.stderr)
        return 1

    with SessionLocal() as session:
        created, present = create_admins(session, password)
        sales_created, sales_present = create_sales(session, password, args.sales)

    # Never print the password or a hash.
    print(f"Bootstrap admins: {created} created, {present} already present.")
    if args.sales:
        print(f"Bootstrap sales: {sales_created} created, {sales_present} already present.")
    print("Accounts created this way must change their password at first login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
