from typing import Any

import psycopg

Row = dict[str, Any]


def get_cart_id(conn: psycopg.Connection, user_id: int) -> int | None:
    row = conn.execute(
        "SELECT id FROM carts WHERE user_id = %s", (user_id,)
    ).fetchone()
    return row["id"] if row else None


def lock_cart(conn: psycopg.Connection, user_id: int) -> int | None:
    """ردیف سبد کاربر را قفل می‌کند تا تغییرات سبد و checkout یک کاربر پشت‌سرهم اجرا شوند."""
    row = conn.execute(
        "SELECT id FROM carts WHERE user_id = %s FOR UPDATE", (user_id,)
    ).fetchone()
    return row["id"] if row else None


def get_or_create_cart(conn: psycopg.Connection, user_id: int) -> int:
    row = conn.execute(
        """
        INSERT INTO carts (user_id) VALUES (%s)
        ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id
        RETURNING id
        """,
        (user_id,),
    ).fetchone()
    return row["id"]


def list_cart_lines(conn: psycopg.Connection, user_id: int) -> list[Row]:
    return conn.execute(
        """
        SELECT ci.id AS item_id, ci.product_id, p.title AS product_title,
               p.price, ci.quantity, p.shop_id, s.name AS shop_name
        FROM cart_items ci
        JOIN carts c ON c.id = ci.cart_id
        JOIN products p ON p.id = ci.product_id
        JOIN shops s ON s.id = p.shop_id
        WHERE c.user_id = %s
        ORDER BY ci.id
        """,
        (user_id,),
    ).fetchall()


def get_item_quantity(conn: psycopg.Connection, cart_id: int, product_id: int) -> int:
    row = conn.execute(
        "SELECT quantity FROM cart_items WHERE cart_id = %s AND product_id = %s",
        (cart_id, product_id),
    ).fetchone()
    return row["quantity"] if row else 0


def upsert_cart_item(
    conn: psycopg.Connection, cart_id: int, product_id: int, quantity: int
) -> Row:
    """آیتم جدید می‌سازد یا تعداد آیتم موجود را زیاد می‌کند؛ inserted مشخص می‌کند کدام."""
    return conn.execute(
        """
        INSERT INTO cart_items (cart_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (cart_id, product_id)
        DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
        RETURNING id AS item_id, product_id, quantity, (xmax = 0) AS inserted
        """,
        (cart_id, product_id, quantity),
    ).fetchone()


def get_user_item(conn: psycopg.Connection, user_id: int, item_id: int) -> Row | None:
    return conn.execute(
        """
        SELECT ci.id AS item_id, ci.product_id, ci.quantity
        FROM cart_items ci JOIN carts c ON c.id = ci.cart_id
        WHERE ci.id = %s AND c.user_id = %s
        """,
        (item_id, user_id),
    ).fetchone()


def set_item_quantity(conn: psycopg.Connection, item_id: int, quantity: int) -> Row:
    return conn.execute(
        """
        UPDATE cart_items SET quantity = %s WHERE id = %s
        RETURNING id AS item_id, product_id, quantity
        """,
        (quantity, item_id),
    ).fetchone()


def delete_user_item(conn: psycopg.Connection, user_id: int, item_id: int) -> bool:
    row = conn.execute(
        """
        DELETE FROM cart_items ci USING carts c
        WHERE ci.cart_id = c.id AND ci.id = %s AND c.user_id = %s
        RETURNING ci.id
        """,
        (item_id, user_id),
    ).fetchone()
    return row is not None


def lock_lines_for_checkout(conn: psycopg.Connection, user_id: int) -> list[Row]:
    """آیتم‌های سبد را می‌خواند و ردیف محصولات را قفل می‌کند.

    ترتیب ثابت (p.id) جلوی deadlock بین دو checkout همزمان را می‌گیرد.
    """
    return conn.execute(
        """
        SELECT ci.id AS item_id, ci.product_id, ci.quantity,
               p.title, p.price, p.stock, p.is_active, p.shop_id
        FROM cart_items ci
        JOIN carts c ON c.id = ci.cart_id
        JOIN products p ON p.id = ci.product_id
        WHERE c.user_id = %s
        ORDER BY p.id
        FOR UPDATE OF p
        """,
        (user_id,),
    ).fetchall()


def clear_cart(conn: psycopg.Connection, user_id: int) -> None:
    conn.execute(
        """
        DELETE FROM cart_items
        WHERE cart_id IN (SELECT id FROM carts WHERE user_id = %s)
        """,
        (user_id,),
    )
