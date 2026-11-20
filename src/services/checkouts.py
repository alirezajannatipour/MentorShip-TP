from collections import defaultdict
from typing import Any

import psycopg

from src.errors import AppError
from src.repositories import addresses as addresses_repo
from src.repositories import carts as carts_repo
from src.repositories import orders as orders_repo
from src.repositories import products as products_repo
from src.repositories import wallet as wallet_repo
from src.schemas.checkouts import CheckoutCreate
from src.services import idempotency


def create_checkout(
    conn: psycopg.Connection,
    user: dict[str, Any],
    idempotency_key: str,
    data: CheckoutCreate,
) -> tuple[int, dict[str, Any]]:
    return idempotency.run_idempotent(
        conn,
        user_id=user["id"],
        key=idempotency_key,
        scope="checkout",
        payload=data.model_dump(mode="json"),
        handler=lambda: _place_order(conn, user["id"], data),
    )


def _place_order(
    conn: psycopg.Connection, user_id: int, data: CheckoutCreate
) -> tuple[int, dict[str, Any]]:
    """همه‌ی مراحل پرداخت؛ در ترنزکشنی اجرا می‌شود که run_idempotent باز کرده است."""
    # ۱) قفل سبد: دو checkout همزمان یک کاربر (مثلاً دوبار کلیک با دو کلید متفاوت)
    #    پشت‌سرهم اجرا می‌شوند و دومی سبد خالی می‌بیند، نه سبد قدیمی.
    if carts_repo.lock_cart(conn, user_id) is None:
        raise AppError(422, "CART_EMPTY", "سبد خرید خالی است.")

    # ۲) قفل ردیف محصولات: دو خریدار همزمان نمی‌توانند آخرین موجودی را با هم بخرند
    lines = carts_repo.lock_lines_for_checkout(conn, user_id)
    if not lines:
        raise AppError(422, "CART_EMPTY", "سبد خرید خالی است.")

    address = addresses_repo.get_active_address(conn, user_id, data.address_id)
    if address is None:
        raise AppError(422, "ADDRESS_NOT_FOUND", "آدرس انتخاب‌شده معتبر نیست.")

    unavailable = [line["product_id"] for line in lines if not line["is_active"]]
    if unavailable:
        raise AppError(
            409,
            "PRODUCT_UNAVAILABLE",
            "بعضی محصولات سبد خرید دیگر در دسترس نیستند.",
            {"product_ids": unavailable},
        )

    total = sum(line["price"] * line["quantity"] for line in lines)
    if total != data.expected_total_price:
        raise AppError(
            409,
            "PRICE_CHANGED",
            "قیمت محصولات تغییر کرده است.",
            {"current_total_price": total},
        )

    for line in lines:
        if not products_repo.reserve_stock(conn, line["product_id"], line["quantity"]):
            raise AppError(
                409,
                "OUT_OF_STOCK",
                "موجودی یکی از محصولات کافی نیست.",
                {"product_id": line["product_id"]},
            )

    balance_after = wallet_repo.debit_if_enough(conn, user_id, total)
    if balance_after is None:
        raise AppError(
            422, "INSUFFICIENT_WALLET_BALANCE", "موجودی کیف پول کافی نیست."
        )

    checkout_id = orders_repo.create_checkout(
        conn,
        user_id=user_id,
        total_price=total,
        receiver_name=data.receiver_name,
        receiver_phone=data.receiver_phone,
        province=address["province"],
        city=address["city"],
        address_detail=address["address_detail"],
        postal_code=address["postal_code"],
    )

    by_shop: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for line in lines:
        by_shop[line["shop_id"]].append(line)

    orders = []
    for shop_id in sorted(by_shop):
        shop_lines = by_shop[shop_id]
        order_total = sum(line["price"] * line["quantity"] for line in shop_lines)
        order_id = orders_repo.create_order(
            conn, checkout_id=checkout_id, shop_id=shop_id, total_price=order_total
        )
        orders_repo.create_order_items(
            conn,
            order_id,
            [(l["product_id"], l["quantity"], l["price"]) for l in shop_lines],
        )
        orders.append(
            {
                "order_id": order_id,
                "shop_id": shop_id,
                "total_price": order_total,
                "status": "paid",
            }
        )

    wallet_repo.insert_transaction(
        conn,
        user_id=user_id,
        amount=total,
        type_="purchase",
        balance_after=balance_after,
        checkout_id=checkout_id,
    )
    carts_repo.clear_cart(conn, user_id)

    return 201, {
        "checkout_id": checkout_id,
        "total_price": total,
        "wallet_balance_after": balance_after,
        "orders": orders,
    }


def get_checkout(
    conn: psycopg.Connection, user: dict[str, Any], checkout_id: int
) -> dict[str, Any]:
    checkout = orders_repo.get_user_checkout(conn, user["id"], checkout_id)
    if checkout is None:
        raise AppError(404, "CHECKOUT_NOT_FOUND", "پرداخت پیدا نشد.")
    checkout["orders"] = orders_repo.list_checkout_orders(conn, checkout_id)
    return checkout
