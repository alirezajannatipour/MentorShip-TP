from typing import Any

import psycopg

from src.errors import AppError
from src.repositories import categories as categories_repo
from src.repositories import products as products_repo
from src.repositories import shops as shops_repo
from src.schemas.products import ProductCreate
from src.utils.pagination import build_pagination


def get_product(conn: psycopg.Connection, product_id: int) -> dict[str, Any]:
    row = products_repo.get_product_details(conn, product_id)
    if row is None:
        raise AppError(404, "PRODUCT_NOT_FOUND", "محصول پیدا نشد.")
    images = products_repo.get_product_images(conn, product_id)
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "price": row["price"],
        "stock": row["stock"],
        "sold_count": row["sold_count"],
        "created_at": row["created_at"],
        "images": images,
        "category": {"id": row["category_id"], "name": row["category_name"]},
        "shop": {
            "id": row["shop_id"],
            "name": row["shop_name"],
            "logo_url": row["shop_logo_url"],
        },
    }


def create_product(
    conn: psycopg.Connection, user: dict[str, Any], data: ProductCreate
) -> dict[str, Any]:
    shop = shops_repo.get_shop(conn, data.shop_id)
    if shop is None:
        raise AppError(422, "SHOP_NOT_FOUND", "غرفه‌ای با این شناسه وجود ندارد.")
    if shop["owner_id"] != user["id"]:
        raise AppError(403, "NOT_SHOP_OWNER", "شما مالک این غرفه نیستید.")
    if not categories_repo.category_exists(conn, data.category_id):
        raise AppError(422, "CATEGORY_NOT_FOUND", "دسته‌بندی‌ای با این شناسه وجود ندارد.")

    product_id = products_repo.create_product(
        conn,
        shop_id=data.shop_id,
        category_id=data.category_id,
        title=data.title,
        description=data.description,
        price=data.price,
        stock=data.stock,
    )
    products_repo.add_images(conn, product_id, data.images)
    conn.commit()
    return get_product(conn, product_id)


def list_products(
    conn: psycopg.Connection,
    *,
    q: str | None,
    category_id: int | None,
    shop_id: int | None,
    sort: str,
    page: int,
    limit: int,
) -> dict[str, Any]:
    total = products_repo.count_products(
        conn, q=q, category_id=category_id, shop_id=shop_id
    )
    items = products_repo.list_products(
        conn,
        q=q,
        category_id=category_id,
        shop_id=shop_id,
        sort=sort,
        limit=limit,
        offset=(page - 1) * limit,
    )
    return {
        "items": items,
        "pagination": build_pagination(total, page, limit),
    }
