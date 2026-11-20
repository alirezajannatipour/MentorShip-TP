from typing import Any

import psycopg

from src.errors import AppError
from src.repositories import addresses as addresses_repo
from src.schemas.addresses import AddressCreate


def list_addresses(conn: psycopg.Connection, user: dict[str, Any]) -> list[dict[str, Any]]:
    return addresses_repo.list_active_addresses(conn, user["id"])


def create_address(
    conn: psycopg.Connection, user: dict[str, Any], data: AddressCreate
) -> dict[str, Any]:
    address = addresses_repo.create_address(
        conn,
        user_id=user["id"],
        province=data.province,
        city=data.city,
        address_detail=data.address_detail,
        postal_code=data.postal_code,
    )
    conn.commit()
    return address


def delete_address(conn: psycopg.Connection, user: dict[str, Any], address_id: int) -> None:
    if not addresses_repo.deactivate_address(conn, user["id"], address_id):
        raise AppError(404, "ADDRESS_NOT_FOUND", "آدرس پیدا نشد.")
    conn.commit()
