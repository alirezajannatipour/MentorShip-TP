from typing import Annotated

from fastapi import APIRouter, Query

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.orders import OrderStatus, ShopOrderList
from src.schemas.shops import ShopCreate, ShopOut, ShopPublic
from src.services import orders as orders_service
from src.services import shops as shops_service

router = APIRouter(prefix="/shops", tags=["shops"])


@router.post("", status_code=201, response_model=ShopOut)
def create_shop(payload: ShopCreate, user: CurrentUser, conn: DbConn):
    return shops_service.create_shop(conn, user, payload)


@router.get("/{shop_id}", response_model=ShopPublic)
def read_shop(shop_id: int, conn: DbConn):
    return shops_service.get_shop(conn, shop_id)


@router.get("/{shop_id}/orders", response_model=ShopOrderList)
def read_shop_orders(
    shop_id: int,
    user: CurrentUser,
    conn: DbConn,
    status: OrderStatus | None = None,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return orders_service.list_shop_orders(conn, user, shop_id, status, page, limit)
