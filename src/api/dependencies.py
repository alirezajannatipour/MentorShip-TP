from collections.abc import Iterator
from typing import Annotated, Any

import psycopg
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.connections.postgresql import pool
from src.errors import AppError
from src.repositories import users as users_repo
from src.utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_conn() -> Iterator[psycopg.Connection]:
    """یک کانکشن از pool می‌دهد و در پایان درخواست پسش می‌دهد."""
    with pool.connection() as conn:
        yield conn


DbConn = Annotated[psycopg.Connection, Depends(get_conn)]


def get_current_user(
    conn: DbConn,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> dict[str, Any]:
    if credentials is None:
        raise AppError(401, "UNAUTHORIZED", "ابتدا وارد شوید.")
    user_id = decode_access_token(credentials.credentials)
    user = users_repo.get_user_by_id(conn, user_id)
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "کاربر این توکن وجود ندارد.")
    return user


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
