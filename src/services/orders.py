from collections import defaultdict
from typing import Any

import psycopg

from src.connections.postgresql import transaction
from src.errors import AppError
from src.repositories import orders as orders_repo
from src.repositories import products as products_repo
from src.repositories import shops as shops_repo
from src.repositories import wallet as wallet_repo
from src.utils.pagination import build_pagination

# (وضعیت فعلی، وضعیت هدف) ← نقش‌هایی که اجازه‌ی این انتقال را دارند
_TRANSITIONS: dict[tuple[str, str], set[str]] = {
    ("paid", "shipping"): {"seller"},
    ("shipping", "delivered"): {"buyer"},
    ("paid", "cancelled"): {"buyer", "seller"},
    ("shipping", "cancelled"): {"seller"},
}


def _not_found() -> AppError:
    return AppError(404, "ORDER_NOT_FOUND", "سفارش پیدا نشد.")


def _group_items(order_ids: list[int], conn: psycopg.Connection) -> dict[int, list]:
    grouped: dict[int, list] = defaultdict(list)
    if order_ids:
        for item in orders_repo.list_order_items(conn, order_ids):
            grouped[item["order_id"]].append(item)
    return grouped


def list_buyer_orders(
    conn: psycopg.Connection,
    user: dict[str, Any],
    status: str | None,
    page: int,
    limit: int,
) -> dict[str, Any]:
    total = orders_repo.count_buyer_orders(conn, user["id"], status)
    items = orders_repo.list_buyer_orders(
        conn, user["id"], status, limit, (page - 1) * limit
    )
    return {"items": items, "pagination": build_pagination(total, page, limit)}


def get_order(
    conn: psycopg.Connection, user: dict[str, Any], order_id: int
) -> dict[str, Any]:
    order = orders_repo.get_order_with_parties(conn, order_id)
    if order is None or user["id"] not in (order["buyer_id"], order["seller_id"]):
        raise _not_found()
    # اطلاعات حساب خریدار/فروشنده (buyer_id و seller_id) در خروجی نمی‌آید؛
    # فقط snapshot گیرنده که برای ارسال لازم است.
    order["items"] = _group_items([order_id], conn)[order_id]
    return order


def list_shop_orders(
    conn: psycopg.Connection,
    user: dict[str, Any],
    shop_id: int,
    status: str | None,
    page: int,
    limit: int,
) -> dict[str, Any]:
    shop = shops_repo.get_shop(conn, shop_id)
    if shop is None:
        raise AppError(404, "SHOP_NOT_FOUND", "غرفه پیدا نشد.")
    if shop["owner_id"] != user["id"]:
        raise AppError(403, "NOT_SHOP_OWNER", "شما مالک این غرفه نیستید.")
    total = orders_repo.count_shop_orders(conn, shop_id, status)
    orders = orders_repo.list_shop_orders(conn, shop_id, status, limit, (page - 1) * limit)
    grouped = _group_items([o["order_id"] for o in orders], conn)
    for order in orders:
        order["items"] = grouped[order["order_id"]]
    return {"items": orders, "pagination": build_pagination(total, page, limit)}


def change_status(
    conn: psycopg.Connection, user: dict[str, Any], order_id: int, target: str
) -> dict[str, Any]:
    with transaction(conn):
        order = orders_repo.get_order_with_parties(conn, order_id, lock=True)
        roles: set[str] = set()
        if order is not None:
            if order["buyer_id"] == user["id"]:
                roles.add("buyer")
            if order["seller_id"] == user["id"]:
                roles.add("seller")
        if not roles:
            raise _not_found()

        allowed_roles = _TRANSITIONS.get((order["status"], target))
        if allowed_roles is None:
            raise AppError(
                409,
                "INVALID_STATUS_TRANSITION",
                "تغییر وضعیت از حالت فعلی ممکن نیست.",
                {"current_status": order["status"]},
            )
        if not roles & allowed_roles:
            raise AppError(
                403, "FORBIDDEN_TRANSITION", "شما اجازه‌ی این تغییر وضعیت را ندارید."
            )

        if target == "delivered":
            _pay_seller(conn, order)
        elif target == "cancelled":
            _refund_buyer(conn, order)
        orders_repo.set_order_status(conn, order_id, target)
    return get_order(conn, user, order_id)


def _pay_seller(conn: psycopg.Connection, order: dict[str, Any]) -> None:
    balance_after = wallet_repo.credit(conn, order["seller_id"], order["total_price"])
    wallet_repo.insert_transaction(
        conn,
        user_id=order["seller_id"],
        amount=order["total_price"],
        type_="sale",
        balance_after=balance_after,
        order_id=order["order_id"],
    )


def _refund_buyer(conn: psycopg.Connection, order: dict[str, Any]) -> None:
    items = orders_repo.list_order_items(conn, [order["order_id"]])
    # ترتیب ثابت product_id، مثل checkout، برای جلوگیری از deadlock
    for item in sorted(items, key=lambda i: i["product_id"]):
        products_repo.restore_stock(conn, item["product_id"], item["quantity"])
    balance_after = wallet_repo.credit(conn, order["buyer_id"], order["total_price"])
    wallet_repo.insert_transaction(
        conn,
        user_id=order["buyer_id"],
        amount=order["total_price"],
        type_="refund",
        balance_after=balance_after,
        order_id=order["order_id"],
    )
