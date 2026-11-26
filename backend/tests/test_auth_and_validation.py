import pytest
from fastapi import HTTPException

from app.schemas import PharmacyRegistration, UserCreate
from app.services.auth import (
    check_login_rate_limit,
    clear_login_failures,
    create_access_token,
    decode_access_token,
    hash_password,
    record_login_failure,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password = "safe-password-123"
    stored = hash_password(password)

    assert stored != password
    assert verify_password(stored, password)
    assert not verify_password(stored, "wrong-password")


def test_access_token_contains_user_identity() -> None:
    token = create_access_token("alice", "pharmacist")

    decoded = decode_access_token(token)

    assert decoded.username == "alice"
    assert decoded.role == "pharmacist"


def test_new_accounts_require_eight_character_passwords() -> None:
    with pytest.raises(ValueError):
        UserCreate(username="alice", full_name="Alice", role="pharmacist", password="short")
    with pytest.raises(ValueError):
        PharmacyRegistration(
            name="Example Pharmacy",
            admin_username="admin",
            admin_full_name="Admin",
            admin_password="short",
        )


def test_login_rate_limit_blocks_after_five_failures() -> None:
    client_key = "rate-limit-test"
    clear_login_failures(client_key)
    for _ in range(5):
        record_login_failure(client_key)

    with pytest.raises(HTTPException) as error:
        check_login_rate_limit(client_key)

    assert getattr(error.value, "status_code", None) == 429
    clear_login_failures(client_key)


def test_role_dependency_rejects_cross_role_access() -> None:
    from app.services.auth import require_roles

    dependency = require_roles("admin")
    from app.models.entities import User

    pharmacist = User(
        username="security-pharmacist",
        full_name="Security Pharmacist",
        role="pharmacist",
        password="not-a-real-password",
        active=True,
    )
    with pytest.raises(HTTPException) as error:
        dependency(pharmacist)

    assert error.value.status_code == 403
