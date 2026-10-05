"""Authentication and JWT behaviour."""

from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def test_register_returns_token_and_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "Reviewer@Example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "reviewer@example.com"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]
    assert body["access_token"]


def test_special_use_email_domain_is_allowed(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "reviewer.a@synthetic.test", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "reviewer.a@synthetic.test"


def test_passwords_are_hashed_not_stored_plaintext(client: TestClient, register_user) -> None:
    register_user("hash-check@example.com", "correct-horse-battery")
    from app.db.session import get_session_factory
    from sqlalchemy import select

    db = get_session_factory()()
    try:
        user = db.scalar(select(User).where(User.email == "hash-check@example.com"))
        assert user is not None
        assert user.password_hash != "correct-horse-battery"
        assert user.password_hash.startswith("$2")
        assert verify_password("correct-horse-battery", user.password_hash)
        assert not verify_password("wrong-password-1", user.password_hash)
    finally:
        db.close()


def test_duplicate_email_is_rejected(client: TestClient, register_user) -> None:
    register_user("dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "DUP@example.com", "password": "another-long-password"},
    )
    assert response.status_code == 409


def test_short_password_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_success_and_failure(client: TestClient, register_user) -> None:
    register_user("login@example.com", "correct-horse-battery")
    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "correct-horse-battery"},
    )
    assert ok.status_code == 200
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "definitely-wrong"},
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid email or password."
    missing = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "correct-horse-battery"},
    )
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Invalid email or password."


def test_me_requires_valid_token(client: TestClient, register_user) -> None:
    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401

    bogus = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert bogus.status_code == 401

    body = register_user("me@example.com")
    ok = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == "me@example.com"


def test_expired_token_is_rejected(client: TestClient, register_user) -> None:
    body = register_user("expired@example.com")
    user_id = body["user"]["id"]
    expired = create_access_token(
        user_id=__import__("uuid").UUID(user_id),
        email="expired@example.com",
        expires_delta=timedelta(seconds=-10),
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_hash_helper_round_trip() -> None:
    hashed = hash_password("correct-horse-battery")
    assert hashed != "correct-horse-battery"
    assert verify_password("correct-horse-battery", hashed)
