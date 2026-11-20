from typing import Any

import psycopg

from src.connections.postgresql import transaction
from src.errors import AppError
from src.repositories import carts as carts_repo
from src.repositories import products as products_repo


def get_cart(conn: psycopg.Connection, user: dict[str, Any]) -> dict[str, Any]:
    items = carts_repo.list_cart_lines(conn, user["id"])
    return {
        "cart_id": carts_repo.get_cart_id(conn, user["id"]),
        "items": items,
        "total_price": sum(i["price"] * i["quantity"] for i in items),
    }


def _out_of_stock(product_id: int, stock: int) -> AppError:
    return AppError(
        409,
        "OUT_OF_STOCK",
        "تعداد درخواستی بیشتر از موجودی محصول است.",
        {"product_id": product_id, "stock": stock},
    )


def add_item(
    conn: psycopg.Connection, user: dict[str, Any], product_id: int, quantity: int
) -> tuple[dict[str, Any], bool]:
    """آیتم را اضافه می‌کند؛ اگر محصول از قبل در سبد باشد تعدادش جمع می‌شود.

    خروجی: (آیتم، آیا جدید ساخته شد؟)
    """
    with transaction(conn):
        product = products_repo.get_active_product_stock(conn, product_id)
        if product is None:
            raise AppError(422, "PRODUCT_NOT_FOUND", "محصول وجود ندارد یا غیرفعال است.")
        cart_id = carts_repo.get_or_create_cart(conn, user["id"])
        existing = carts_repo.get_item_quantity(conn, cart_id, product_id)
        if existing + quantity > product["stock"]:
            raise _out_of_stock(product_id, product["stock"])
        row = carts_repo.upsert_cart_item(conn, cart_id, product_id, quantity)
    created = row.pop("inserted")
    return row, created


def update_item(
    conn: psycopg.Connection, user: dict[str, Any], item_id: int, quantity: int
) -> dict[str, Any]:
    with transaction(conn):
        carts_repo.lock_cart(conn, user["id"])
        item = carts_repo.get_user_item(conn, user["id"], item_id)
        if item is None:
            raise AppError(404, "CART_ITEM_NOT_FOUND", "آیتم سبد خرید پیدا نشد.")
        product = products_repo.get_active_product_stock(conn, item["product_id"])
        if product is None:
            raise AppError(409, "PRODUCT_UNAVAILABLE", "این محصول دیگر در دسترس نیست.")
        if quantity > product["stock"]:
            raise _out_of_stock(item["product_id"], product["stock"])
        return carts_repo.set_item_quantity(conn, item_id, quantity)


def delete_item(conn: psycopg.Connection, user: dict[str, Any], item_id: int) -> None:
    with transaction(conn):
        carts_repo.lock_cart(conn, user["id"])
        if not carts_repo.delete_user_item(conn, user["id"], item_id):
            raise AppError(404, "CART_ITEM_NOT_FOUND", "آیتم سبد خرید پیدا نشد.")
