from typing import Any

import psycopg

Row = dict[str, Any]

_RECEIVER = (
    "c.receiver_name, c.receiver_phone, c.province, c.city, "
    "c.address_detail, c.postal_code"
)


def create_checkout(
    conn: psycopg.Connection,
    *,
    user_id: int,
    total_price: int,
    receiver_name: str,
    receiver_phone: str,
    province: str,
    city: str,
    address_detail: str,
    postal_code: str | None,
) -> int:
    row = conn.execute(
        """
        INSERT INTO checkouts
            (user_id, total_price, receiver_name, receiver_phone,
             province, city, address_detail, postal_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            user_id,
            total_price,
            receiver_name,
            receiver_phone,
            province,
            city,
            address_detail,
            postal_code,
        ),
    ).fetchone()
    return row["id"]


def create_order(
    conn: psycopg.Connection, *, checkout_id: int, shop_id: int, total_price: int
) -> int:
    row = conn.execute(
        """
        INSERT INTO orders (checkout_id, shop_id, total_price, status)
        VALUES (%s, %s, %s, 'paid')
        RETURNING id
        """,
        (checkout_id, shop_id, total_price),
    ).fetchone()
    return row["id"]


def create_order_items(
    conn: psycopg.Connection, order_id: int, items: list[tuple[int, int, int]]
) -> None:
    """items: لیست (product_id, quantity, price_at_purchase)"""
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
            VALUES (%s, %s, %s, %s)
            """,
            [(order_id, pid, qty, price) for pid, qty, price in items],
        )


def get_user_checkout(
    conn: psycopg.Connection, user_id: int, checkout_id: int
) -> Row | None:
    return conn.execute(
        """
        SELECT id AS checkout_id, total_price, payment_method::text AS payment_method,
               receiver_name, receiver_phone, province, city, address_detail,
               postal_code, created_at
        FROM checkouts WHERE id = %s AND user_id = %s
        """,
        (checkout_id, user_id),
    ).fetchone()


def list_checkout_orders(conn: psycopg.Connection, checkout_id: int) -> list[Row]:
    return conn.execute(
        """
        SELECT id AS order_id, shop_id, total_price, status::text AS status
        FROM orders WHERE checkout_id = %s ORDER BY id
        """,
        (checkout_id,),
    ).fetchall()


def _status_filter(status: str | None, params: list[Any]) -> str:
    if status is None:
        return ""
    params.append(status)
    return " AND o.status = %s::order_status"


def count_buyer_orders(
    conn: psycopg.Connection, user_id: int, status: str | None
) -> int:
    params: list[Any] = [user_id]
    extra = _status_filter(status, params)
    row = conn.execute(
        f"""
        SELECT count(*) AS total
        FROM orders o JOIN checkouts c ON c.id = o.checkout_id
        WHERE c.user_id = %s{extra}
        """,
        params,
    ).fetchone()
    return row["total"]


def list_buyer_orders(
    conn: psycopg.Connection, user_id: int, status: str | None, limit: int, offset: int
) -> list[Row]:
    params: list[Any] = [user_id]
    extra = _status_filter(status, params)
    return conn.execute(
        f"""
        SELECT o.id AS order_id, o.checkout_id, o.shop_id, s.name AS shop_name,
               o.total_price, o.status::text AS status, o.created_at
        FROM orders o
        JOIN checkouts c ON c.id = o.checkout_id
        JOIN shops s ON s.id = o.shop_id
        WHERE c.user_id = %s{extra}
        ORDER BY o.id DESC
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
    ).fetchall()


def count_shop_orders(
    conn: psycopg.Connection, shop_id: int, status: str | None
) -> int:
    params: list[Any] = [shop_id]
    extra = _status_filter(status, params)
    row = conn.execute(
        f"SELECT count(*) AS total FROM orders o WHERE o.shop_id = %s{extra}", params
    ).fetchone()
    return row["total"]


def list_shop_orders(
    conn: psycopg.Connection, shop_id: int, status: str | None, limit: int, offset: int
) -> list[Row]:
    params: list[Any] = [shop_id]
    extra = _status_filter(status, params)
    return conn.execute(
        f"""
        SELECT o.id AS order_id, o.status::text AS status, o.total_price, o.created_at,
               {_RECEIVER}
        FROM orders o JOIN checkouts c ON c.id = o.checkout_id
        WHERE o.shop_id = %s{extra}
        ORDER BY o.id DESC
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
    ).fetchall()


def get_order_with_parties(
    conn: psycopg.Connection, order_id: int, *, lock: bool = False
) -> Row | None:
    """سفارش همراه خریدار، مالک غرفه و snapshot گیرنده. با lock=True ردیف سفارش قفل می‌شود."""
    lock_sql = "FOR UPDATE OF o" if lock else ""
    return conn.execute(
        f"""
        SELECT o.id AS order_id, o.checkout_id, o.shop_id, o.total_price,
               o.status::text AS status, o.created_at,
               c.user_id AS buyer_id, s.owner_id AS seller_id,
               {_RECEIVER}
        FROM orders o
        JOIN checkouts c ON c.id = o.checkout_id
        JOIN shops s ON s.id = o.shop_id
        WHERE o.id = %s
        {lock_sql}
        """,
        (order_id,),
    ).fetchone()


def list_order_items(conn: psycopg.Connection, order_ids: list[int]) -> list[Row]:
    return conn.execute(
        """
        SELECT oi.order_id, oi.product_id, p.title, oi.quantity, oi.price_at_purchase
        FROM order_items oi JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ANY(%s)
        ORDER BY oi.order_id, oi.id
        """,
        (order_ids,),
    ).fetchall()


def set_order_status(conn: psycopg.Connection, order_id: int, status: str) -> None:
    conn.execute(
        "UPDATE orders SET status = %s::order_status WHERE id = %s", (status, order_id)
    )
