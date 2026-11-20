import hashlib
import json
from collections.abc import Callable
from typing import Any

import psycopg

from src.connections.postgresql import transaction
from src.errors import AppError
from src.repositories import idempotency as idempotency_repo


def _request_hash(scope: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"scope": scope, "body": payload}, sort_keys=True, ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_idempotent(
    conn: psycopg.Connection,
    *,
    user_id: int,
    key: str,
    scope: str,
    payload: dict[str, Any],
    handler: Callable[[], tuple[int, dict[str, Any]]],
) -> tuple[int, dict[str, Any]]:
    """handler را فقط یک بار برای (user_id, key) اجرا می‌کند.

    کل کار (رزرو کلید، تغییرات handler و ذخیره‌ی پاسخ) در یک ترنزکشن است:
    - تکرار با همان کلید و بدنه: همان پاسخ اول، بدون اجرای دوباره.
    - همان کلید با بدنه‌ی دیگر: 409.
    - دو درخواست همزمان با یک کلید: دومی صبر می‌کند تا اولی تمام شود، بعد پاسخ اولی را می‌گیرد.
    - خطا در handler: همه‌چیز rollback می‌شود، از جمله رزرو کلید.
    """
    request_hash = _request_hash(scope, payload)
    with transaction(conn):
        claim_id = idempotency_repo.try_claim(conn, user_id, key, request_hash)
        if claim_id is None:
            existing = idempotency_repo.get_existing(conn, user_id, key)
            if existing is None or existing["request_hash"] != request_hash:
                raise AppError(
                    409,
                    "IDEMPOTENCY_KEY_REUSED",
                    "این کلید قبلاً با درخواست دیگری استفاده شده است.",
                )
            if existing["response_status"] is None:
                raise AppError(
                    409, "REQUEST_IN_PROGRESS", "این درخواست هنوز در حال پردازش است."
                )
            return existing["response_status"], existing["response_body"]

        status, body = handler()
        idempotency_repo.store_response(conn, claim_id, status, body)
        return status, body
