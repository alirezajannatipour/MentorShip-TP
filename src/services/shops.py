from typing import Any

import psycopg

from src.errors import AppError
from src.repositories import shops as shops_repo
from src.schemas.shops import ShopCreate


def create_shop(
    conn: psycopg.Connection, owner: dict[str, Any], data: ShopCreate
) -> dict[str, Any]:
    shop = shops_repo.create_shop(
        conn,
        owner_id=owner["id"],
        name=data.name,
        description=data.description,
        logo_url=data.logo_url,
    )
    conn.commit()
    return shop


def get_shop(conn: psycopg.Connection, shop_id: int) -> dict[str, Any]:
    shop = shops_repo.get_shop(conn, shop_id)
    if shop is None:
        raise AppError(404, "SHOP_NOT_FOUND", "غرفه پیدا نشد.")
    return shop


def list_my_shops(
    conn: psycopg.Connection, owner: dict[str, Any]
) -> list[dict[str, Any]]:
    return shops_repo.list_shops_by_owner(conn, owner["id"])
