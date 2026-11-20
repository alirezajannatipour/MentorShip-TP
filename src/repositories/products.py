from typing import Any

import psycopg

Row = dict[str, Any]

# مقدار sort از کاربر فقط کلید این دیکشنری است؛ خود SQL ثابت و امن است.
_SORT_SQL = {
    "price": "p.price ASC, p.id ASC",
    "-price": "p.price DESC, p.id DESC",
    "-sold_count": "p.sold_count DESC, p.id DESC",
    "-created_at": "p.created_at DESC, p.id DESC",
}


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_filters(
    q: str | None, category_id: int | None, shop_id: int | None
) -> tuple[str, list[Any]]:
    conditions = ["p.is_active = TRUE"]
    params: list[Any] = []
    if q:
        conditions.append("p.title ILIKE %s")
        params.append(f"%{_escape_like(q)}%")
    if category_id is not None:
        conditions.append("p.category_id = %s")
        params.append(category_id)
    if shop_id is not None:
        conditions.append("p.shop_id = %s")
        params.append(shop_id)
    return " AND ".join(conditions), params


def create_product(
    conn: psycopg.Connection,
    *,
    shop_id: int,
    category_id: int,
    title: str,
    description: str | None,
    price: int,
    stock: int,
) -> int:
    row = conn.execute(
        """
        INSERT INTO products (shop_id, category_id, title, description, price, stock)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (shop_id, category_id, title, description, price, stock),
    ).fetchone()
    return row["id"]


def add_images(conn: psycopg.Connection, product_id: int, urls: list[str]) -> None:
    if not urls:
        return
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO product_images (product_id, image_url, sort_order)
            VALUES (%s, %s, %s)
            """,
            [(product_id, url, index) for index, url in enumerate(urls)],
        )


def get_product_details(conn: psycopg.Connection, product_id: int) -> Row | None:
    return conn.execute(
        """
        SELECT p.id, p.title, p.description, p.price, p.stock, p.sold_count,
               p.created_at,
               c.id AS category_id, c.name AS category_name,
               s.id AS shop_id, s.name AS shop_name, s.logo_url AS shop_logo_url
        FROM products p
        JOIN categories c ON c.id = p.category_id
        JOIN shops s ON s.id = p.shop_id
        WHERE p.id = %s AND p.is_active = TRUE
        """,
        (product_id,),
    ).fetchone()


def get_product_images(conn: psycopg.Connection, product_id: int) -> list[Row]:
    return conn.execute(
        """
        SELECT image_url AS url, sort_order
        FROM product_images
        WHERE product_id = %s
        ORDER BY sort_order, id
        """,
        (product_id,),
    ).fetchall()


def count_products(
    conn: psycopg.Connection,
    *,
    q: str | None,
    category_id: int | None,
    shop_id: int | None,
) -> int:
    where, params = _build_filters(q, category_id, shop_id)
    row = conn.execute(
        f"SELECT count(*) AS total FROM products p WHERE {where}", params
    ).fetchone()
    return row["total"]


def list_products(
    conn: psycopg.Connection,
    *,
    q: str | None,
    category_id: int | None,
    shop_id: int | None,
    sort: str,
    limit: int,
    offset: int,
) -> list[Row]:
    where, params = _build_filters(q, category_id, shop_id)
    order_by = _SORT_SQL[sort]
    return conn.execute(
        f"""
        SELECT p.id, p.title, p.price,
               (p.stock > 0) AS in_stock,
               (SELECT pi.image_url FROM product_images pi
                WHERE pi.product_id = p.id
                ORDER BY pi.sort_order, pi.id LIMIT 1) AS main_image_url,
               s.name AS shop_name,
               c.name AS category_name
        FROM products p
        JOIN shops s ON s.id = p.shop_id
        JOIN categories c ON c.id = p.category_id
        WHERE {where}
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
    ).fetchall()


def get_active_product_stock(conn: psycopg.Connection, product_id: int) -> Row | None:
    return conn.execute(
        "SELECT id, stock FROM products WHERE id = %s AND is_active = TRUE",
        (product_id,),
    ).fetchone()


def reserve_stock(conn: psycopg.Connection, product_id: int, quantity: int) -> bool:
    """اتمیک: فقط اگر موجودی کافی باشد کم می‌کند و sold_count را زیاد می‌کند."""
    row = conn.execute(
        """
        UPDATE products
        SET stock = stock - %s, sold_count = sold_count + %s
        WHERE id = %s AND stock >= %s
        RETURNING id
        """,
        (quantity, quantity, product_id, quantity),
    ).fetchone()
    return row is not None


def restore_stock(conn: psycopg.Connection, product_id: int, quantity: int) -> None:
    conn.execute(
        """
        UPDATE products
        SET stock = stock + %s, sold_count = GREATEST(sold_count - %s, 0)
        WHERE id = %s
        """,
        (quantity, quantity, product_id),
    )
