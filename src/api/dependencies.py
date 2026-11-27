from collections.abc import AsyncIterator
from typing import Annotated, Any

import anyio
import psycopg
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings
from src.connections.postgresql import get_slots, pool
from src.errors import AppError
from src.repositories import users as users_repo
from src.utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _release(conn: psycopg.Connection, failed: bool) -> None:
    try:
        if failed:
            conn.rollback()
        else:
            conn.commit()
    finally:
        pool.putconn(conn)


async def get_conn() -> AsyncIterator[psycopg.Connection]:
    """یک کانکشن به‌ازای هر درخواست.

    ابتدا یک «جای خالی» می‌گیرد (حداکثر به اندازه‌ی pool)؛ اگر نبود، بدون اشغال thread در صف
    async منتظر می‌ماند و بعد از db_acquire_timeout ثانیه 503 می‌دهد. بعدش کانکشن
    گرفتن و برگرداندن در threadهای جدا انجام می‌شود تا event loop قفل نشود.
    """
    slots = get_slots()
    try:
        with anyio.fail_after(settings.db_acquire_timeout):
            await slots.acquire()
    except TimeoutError:
        raise AppError(
            503, "SERVICE_BUSY", "سرور شلوغ است؛ کمی بعد دوباره تلاش کنید."
        ) from None
    try:
        conn = await anyio.to_thread.run_sync(pool.getconn)
        failed = False
        try:
            yield conn
        except BaseException:
            failed = True
            raise
        finally:
            with anyio.CancelScope(shield=True):
                await anyio.to_thread.run_sync(_release, conn, failed)
    finally:
        slots.release()


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


def get_idempotency_key(
    idempotency_key: Annotated[str | None, Header()] = None,
) -> str:
    key = (idempotency_key or "").strip()
    if not key:
        raise AppError(
            422, "IDEMPOTENCY_KEY_REQUIRED", "هدر Idempotency-Key الزامی است."
        )
    if len(key) > 100:
        raise AppError(
            422, "IDEMPOTENCY_KEY_INVALID", "Idempotency-Key حداکثر ۱۰۰ کاراکتر است."
        )
    return key


IdempotencyKey = Annotated[str, Depends(get_idempotency_key)]
