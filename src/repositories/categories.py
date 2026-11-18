from typing import Any

import psycopg

Row = dict[str, Any]


def list_categories(conn: psycopg.Connection) -> list[Row]:
    return conn.execute(
        "SELECT id, name, parent_id FROM categories ORDER BY id"
    ).fetchall()


def category_exists(conn: psycopg.Connection, category_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 AS found FROM categories WHERE id = %s", (category_id,)
    ).fetchone()
    return row is not None
