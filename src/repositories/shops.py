from typing import Any

import psycopg

Row = dict[str, Any]


def create_shop(
    conn: psycopg.Connection,
    *,
    owner_id: int,
    name: str,
    description: str | None,
    logo_url: str | None,
) -> Row:
    return conn.execute(
        """
        INSERT INTO shops (owner_id, name, description, logo_url)
        VALUES (%s, %s, %s, %s)
        RETURNING id, owner_id, name, description, logo_url, created_at
        """,
        (owner_id, name, description, logo_url),
    ).fetchone()


def get_shop(conn: psycopg.Connection, shop_id: int) -> Row | None:
    return conn.execute(
        """
        SELECT id, owner_id, name, description, logo_url, created_at
        FROM shops WHERE id = %s
        """,
        (shop_id,),
    ).fetchone()


def list_shops_by_owner(conn: psycopg.Connection, owner_id: int) -> list[Row]:
    return conn.execute(
        """
        SELECT id, owner_id, name, description, logo_url, created_at
        FROM shops WHERE owner_id = %s ORDER BY id
        """,
        (owner_id,),
    ).fetchall()
