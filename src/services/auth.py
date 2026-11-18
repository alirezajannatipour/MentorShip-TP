from typing import Any

import psycopg
from psycopg import errors as pg_errors

from src.errors import AppError
from src.repositories import users as users_repo
from src.schemas.auth import LoginRequest, RegisterRequest
from src.utils.security import (
    burn_password_check,
    create_access_token,
    hash_password,
    verify_password,
)

# نام constraint یا ایندکس یکتا ← عنوان فیلد
_UNIQUE_FIELD_LABELS = {
    "users_email_key": "ایمیل",
    "users_username_lower_key": "نام کاربری",
    "users_phone_number_key": "شماره تلفن",
}


def register_user(conn: psycopg.Connection, data: RegisterRequest) -> dict[str, Any]:
    password_hash = hash_password(data.password)
    try:
        user = users_repo.create_user(
            conn,
            username=data.username,
            email=data.email.lower(),
            phone_number=data.phone_number,
            password_hash=password_hash,
        )
    except pg_errors.UniqueViolation as exc:
        conn.rollback()
        label = _UNIQUE_FIELD_LABELS.get(exc.diag.constraint_name, "اطلاعات")
        raise AppError(
            409, "USER_ALREADY_EXISTS", f"کاربری با این {label} قبلاً ثبت شده است."
        ) from exc
    conn.commit()
    return {"user": user, "token": create_access_token(user["id"])}


def login(conn: psycopg.Connection, data: LoginRequest) -> dict[str, str]:
    if data.email is not None:
        user = users_repo.get_user_with_hash_by_email(conn, data.email.lower())
    else:
        user = users_repo.get_user_with_hash_by_username(conn, data.username)

    invalid = AppError(401, "INVALID_CREDENTIALS", "اطلاعات ورود نادرست است.")
    if user is None:
        burn_password_check(data.password)
        raise invalid
    if not verify_password(user["password_hash"], data.password):
        raise invalid
    return {"token": create_access_token(user["id"])}
