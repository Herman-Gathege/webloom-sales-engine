"""Sprint 3: authentication, roles, logout, and bootstrap safety."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bootstrap import ADMIN_EMAILS, create_admins, create_sales
from app.config import get_settings
from app.models import User, UserRole
from app.security import hash_password

PASSWORD = "correct-horse-battery"

MakeUser = Callable[..., User]


@pytest.fixture
def make_user(session: Session) -> MakeUser:
    def factory(
        email: str = "seller@example.test",
        password: str = PASSWORD,
        role: UserRole = UserRole.SALES,
        is_active: bool = True,
        must_change_password: bool = False,
    ) -> User:
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
            must_change_password=must_change_password,
        )
        session.add(user)
        session.flush()
        return user

    return factory


def login(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_succeeds_and_returns_a_usable_token(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="Admin@Example.test", role=UserRole.ADMIN)

    response = login(anonymous_client, "admin@example.test")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@example.test"
    assert body["user"]["role"] == "admin"
    # The user shape carries the *flag*, never a hash or the password itself.
    assert set(body["user"]) == {
        "id",
        "email",
        "role",
        "is_active",
        "must_change_password",
        "created_at",
    }
    assert "password_hash" not in response.text
    assert PASSWORD not in response.text

    me = anonymous_client.get("/api/v1/auth/me", headers=bearer(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.test"


def test_wrong_password_and_unknown_email_are_indistinguishable(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="seller@example.test")

    wrong = login(anonymous_client, "seller@example.test", "not-the-password")
    unknown = login(anonymous_client, "nobody@example.test", "not-the-password")

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.headers.get("www-authenticate") == "Bearer"


def test_inactive_account_cannot_sign_in(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="gone@example.test", is_active=False)

    response = login(anonymous_client, "gone@example.test")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_passwords_are_stored_as_hashes(
    anonymous_client: TestClient, make_user: MakeUser, session: Session
) -> None:
    user = make_user(email="hash@example.test")
    session.refresh(user)

    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$2")
    assert PASSWORD not in user.password_hash

    response = login(anonymous_client, "hash@example.test")
    assert response.status_code == 200
    assert PASSWORD not in response.text
    assert "password_hash" not in response.text


def test_protected_endpoints_reject_missing_invalid_and_expired_tokens(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    user = make_user()
    settings = get_settings()

    missing = anonymous_client.get("/api/v1/leads")
    assert missing.status_code == 401

    invalid = anonymous_client.get("/api/v1/leads", headers=bearer("not-a-token"))
    assert invalid.status_code == 401

    expired = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "ver": user.token_version,
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    expired_response = anonymous_client.get("/api/v1/leads", headers=bearer(expired))
    assert expired_response.status_code == 401


def test_logout_invalidates_the_token(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="leaver@example.test")
    token = login(anonymous_client, "leaver@example.test").json()["access_token"]

    assert anonymous_client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 200

    logout = anonymous_client.post("/api/v1/auth/logout", headers=bearer(token))
    assert logout.status_code == 204

    after = anonymous_client.get("/api/v1/auth/me", headers=bearer(token))
    assert after.status_code == 401


def test_sales_is_allowed_on_leads_and_refused_on_admin_users(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="sales@example.test", role=UserRole.SALES)
    token = login(anonymous_client, "sales@example.test").json()["access_token"]

    leads = anonymous_client.get("/api/v1/leads", headers=bearer(token))
    assert leads.status_code == 200

    users = anonymous_client.get("/api/v1/users", headers=bearer(token))
    assert users.status_code == 403
    assert users.json()["detail"] == "Administrator access required"


def test_admin_can_list_users_without_leaking_hashes(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="admin@example.test", role=UserRole.ADMIN)
    make_user(email="sales@example.test", role=UserRole.SALES)
    token = login(anonymous_client, "admin@example.test").json()["access_token"]

    response = anonymous_client.get("/api/v1/users", headers=bearer(token))

    assert response.status_code == 200
    emails = {user["email"] for user in response.json()}
    assert {"admin@example.test", "sales@example.test"} <= emails
    assert "password_hash" not in response.text


def test_change_password_reissues_a_token_and_kills_the_old_one(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="changer@example.test", must_change_password=True)
    token = login(anonymous_client, "changer@example.test").json()["access_token"]

    response = anonymous_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "a-much-better-secret"},
        headers=bearer(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["must_change_password"] is False
    assert body["access_token"] != token

    # The old token is dead, the new one works, and the new password signs in.
    assert anonymous_client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 401
    assert (
        anonymous_client.get("/api/v1/auth/me", headers=bearer(body["access_token"])).status_code
        == 200
    )
    changed = login(anonymous_client, "changer@example.test", "a-much-better-secret")
    assert changed.status_code == 200
    assert login(anonymous_client, "changer@example.test", PASSWORD).status_code == 401


def test_change_password_rejects_a_wrong_current_password(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="wrong@example.test")
    token = login(anonymous_client, "wrong@example.test").json()["access_token"]

    response = anonymous_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "nope", "new_password": "a-much-better-secret"},
        headers=bearer(token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The current password is incorrect."


def test_temporary_password_cannot_reach_business_data_until_changed(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="first-login@example.test", must_change_password=True)
    token = login(anonymous_client, "first-login@example.test").json()["access_token"]

    # The session exists, but the lead desk is refused by the API itself.
    assert anonymous_client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 200
    blocked = anonymous_client.get("/api/v1/leads", headers=bearer(token))
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Set a new password before continuing"

    changed = anonymous_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "a-much-better-secret"},
        headers=bearer(token),
    )
    assert changed.status_code == 200

    allowed = anonymous_client.get(
        "/api/v1/leads", headers=bearer(changed.json()["access_token"])
    )
    assert allowed.status_code == 200


def test_bootstrap_creates_four_admins_and_is_idempotent(session: Session) -> None:
    first = create_admins(session, "temporary-password-1")
    second = create_admins(session, "temporary-password-1")

    assert first == (4, 0)
    assert second == (0, 4)

    users = session.scalars(select(User).where(User.email.in_(ADMIN_EMAILS))).all()
    assert len(users) == 4
    assert {user.email for user in users} == set(ADMIN_EMAILS)
    assert {user.role for user in users} == {UserRole.ADMIN}
    assert all(user.must_change_password for user in users)


def test_sales_accounts_can_be_created_idempotently(session: Session) -> None:
    first = create_sales(session, "temporary-password-1", ["reviewer@example.test"])
    second = create_sales(session, "temporary-password-1", ["reviewer@example.test"])

    assert first == (1, 0)
    assert second == (0, 1)

    user = session.scalar(select(User).where(User.email == "reviewer@example.test"))
    assert user is not None
    assert user.role is UserRole.SALES
    assert user.must_change_password


def test_lead_operations_still_work_with_a_real_token(
    anonymous_client: TestClient, make_user: MakeUser
) -> None:
    make_user(email="worker@example.test", role=UserRole.SALES)
    token = login(anonymous_client, "worker@example.test").json()["access_token"]

    response = anonymous_client.get("/api/v1/leads?limit=1", headers=bearer(token))

    assert response.status_code == 200
    assert "items" in response.json()
