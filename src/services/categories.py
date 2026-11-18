from typing import Any

import psycopg

from src.repositories import categories as categories_repo


def list_categories(conn: psycopg.Connection) -> list[dict[str, Any]]:
    return categories_repo.list_categories(conn)
