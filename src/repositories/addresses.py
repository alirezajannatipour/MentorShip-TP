from typing import Any

import psycopg

Row = dict[str, Any]

_COLUMNS = "id, province, city, address_detail, postal_code"


def create_address(
    conn: psycopg.Connection,
    *,
    user_id: int,
    province: str,
    city: str,
    address_detail: str,
    postal_code: str | None,
) -> Row:
    return conn.execute(
        """
        INSERT INTO addresses (user_id, province, city, address_detail, postal_code)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, province, city, address_detail, postal_code
        """,
        (user_id, province, city, address_detail, postal_code),
    ).fetchone()


def list_active_addresses(conn: psycopg.Connection, user_id: int) -> list[Row]:
    return conn.execute(
        """
        SELECT id, province, city, address_detail, postal_code
        FROM addresses WHERE user_id = %s AND is_active = TRUE ORDER BY id
        """,
        (user_id,),
    ).fetchall()


def get_active_address(
    conn: psycopg.Connection, user_id: int, address_id: int
) -> Row | None:
    return conn.execute(
        """
        SELECT id, province, city, address_detail, postal_code
        FROM addresses
        WHERE id = %s AND user_id = %s AND is_active = TRUE
        """,
        (address_id, user_id),
    ).fetchone()


def deactivate_address(conn: psycopg.Connection, user_id: int, address_id: int) -> bool:
    row = conn.execute(
        """
        UPDATE addresses SET is_active = FALSE
        WHERE id = %s AND user_id = %s AND is_active = TRUE
        RETURNING id
        """,
        (address_id, user_id),
    ).fetchone()
    return row is not None
