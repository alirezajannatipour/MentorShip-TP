from typing import Any

import psycopg

Row = dict[str, Any]

_COLUMNS = "id, username, email, phone_number, wallet_balance, created_at"


def create_user(
    conn: psycopg.Connection,
    *,
    username: str,
    email: str,
    phone_number: str,
    password_hash: str,
) -> Row:
    return conn.execute(
        """
        INSERT INTO users (username, email, phone_number, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING id, username, email, phone_number, wallet_balance, created_at
        """,
        (username, email, phone_number, password_hash),
    ).fetchone()


def get_user_by_id(conn: psycopg.Connection, user_id: int) -> Row | None:
    return conn.execute(
        """
        SELECT id, username, email, phone_number, wallet_balance, created_at
        FROM users WHERE id = %s
        """,
        (user_id,),
    ).fetchone()


def get_user_with_hash_by_email(conn: psycopg.Connection, email: str) -> Row | None:
    return conn.execute(
        "SELECT id, password_hash FROM users WHERE email = %s", (email,)
    ).fetchone()


def get_user_with_hash_by_username(
    conn: psycopg.Connection, username: str
) -> Row | None:
    return conn.execute(
        "SELECT id, password_hash FROM users WHERE lower(username) = lower(%s)",
        (username,),
    ).fetchone()
