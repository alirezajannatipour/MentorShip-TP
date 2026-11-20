from typing import Any

import psycopg

Row = dict[str, Any]


def get_balance(conn: psycopg.Connection, user_id: int) -> int:
    row = conn.execute(
        "SELECT wallet_balance FROM users WHERE id = %s", (user_id,)
    ).fetchone()
    return row["wallet_balance"]


def credit(conn: psycopg.Connection, user_id: int, amount: int) -> int:
    """مبلغ را به کیف پول اضافه می‌کند و موجودی جدید را برمی‌گرداند (ردیف قفل می‌شود)."""
    row = conn.execute(
        """
        UPDATE users SET wallet_balance = wallet_balance + %s
        WHERE id = %s RETURNING wallet_balance
        """,
        (amount, user_id),
    ).fetchone()
    return row["wallet_balance"]


def debit_if_enough(conn: psycopg.Connection, user_id: int, amount: int) -> int | None:
    """اتمیک: فقط اگر موجودی کافی باشد کم می‌کند؛ وگرنه None برمی‌گرداند."""
    row = conn.execute(
        """
        UPDATE users SET wallet_balance = wallet_balance - %s
        WHERE id = %s AND wallet_balance >= %s
        RETURNING wallet_balance
        """,
        (amount, user_id, amount),
    ).fetchone()
    return row["wallet_balance"] if row else None


def insert_transaction(
    conn: psycopg.Connection,
    *,
    user_id: int,
    amount: int,
    type_: str,
    balance_after: int,
    checkout_id: int | None = None,
    order_id: int | None = None,
) -> Row:
    return conn.execute(
        """
        INSERT INTO transactions
            (user_id, amount, type, checkout_id, order_id, balance_after)
        VALUES (%s, %s, %s::transaction_type, %s, %s, %s)
        RETURNING id, type, amount, balance_after, checkout_id, order_id, created_at
        """,
        (user_id, amount, type_, checkout_id, order_id, balance_after),
    ).fetchone()


def count_transactions(conn: psycopg.Connection, user_id: int) -> int:
    row = conn.execute(
        "SELECT count(*) AS total FROM transactions WHERE user_id = %s", (user_id,)
    ).fetchone()
    return row["total"]


def list_transactions(
    conn: psycopg.Connection, user_id: int, limit: int, offset: int
) -> list[Row]:
    return conn.execute(
        """
        SELECT id, type, amount, balance_after, checkout_id, order_id, created_at
        FROM transactions WHERE user_id = %s
        ORDER BY id DESC LIMIT %s OFFSET %s
        """,
        (user_id, limit, offset),
    ).fetchall()
