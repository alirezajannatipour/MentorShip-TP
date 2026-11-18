from typing import Annotated, Literal

from fastapi import APIRouter, Query

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.products import ProductCreate, ProductDetail, ProductList
from src.services import products as products_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductList)
def list_products(
    conn: DbConn,
    q: Annotated[str | None, Query(max_length=100)] = None,
    category_id: int | None = None,
    shop_id: int | None = None,
    sort: Literal["price", "-price", "-sold_count", "-created_at"] = "-created_at",
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return products_service.list_products(
        conn,
        q=q,
        category_id=category_id,
        shop_id=shop_id,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.post("", status_code=201, response_model=ProductDetail)
def create_product(payload: ProductCreate, user: CurrentUser, conn: DbConn):
    return products_service.create_product(conn, user, payload)


@router.get("/{product_id}", response_model=ProductDetail)
def read_product(product_id: int, conn: DbConn):
    return products_service.get_product(conn, product_id)
