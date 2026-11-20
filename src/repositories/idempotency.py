from typing import Any

import psycopg
from psycopg.types.json import Jsonb

Row = dict[str, Any]


def try_claim(
    conn: psycopg.Connection, user_id: int, key: str, request_hash: str
) -> int | None:
    """کلید را برای این درخواست رزرو می‌کند.

    اگر همین کلید همزمان توسط ترنزکشن دیگری در حال استفاده باشد، این دستور صبر
    می‌کند تا آن ترنزکشن تمام شود. اگر کلید از قبل ثبت شده باشد None برمی‌گردد.
    """
    row = conn.execute(
        """
        INSERT INTO idempotency_keys (user_id, key, request_hash)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, key) DO NOTHING
        RETURNING id
        """,
        (user_id, key, request_hash),
    ).fetchone()
    return row["id"] if row else None


def get_existing(conn: psycopg.Connection, user_id: int, key: str) -> Row | None:
    return conn.execute(
        """
        SELECT request_hash, response_status, response_body
        FROM idempotency_keys WHERE user_id = %s AND key = %s
        """,
        (user_id, key),
    ).fetchone()


def store_response(
    conn: psycopg.Connection, claim_id: int, status: int, body: dict[str, Any]
) -> None:
    conn.execute(
        """
        UPDATE idempotency_keys SET response_status = %s, response_body = %s
        WHERE id = %s
        """,
        (status, Jsonb(body), claim_id),
    )
