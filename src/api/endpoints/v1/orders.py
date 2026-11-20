from typing import Annotated

from fastapi import APIRouter, Query

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.orders import (
    OrderDetail,
    OrderList,
    OrderStatus,
    OrderStatusUpdate,
)
from src.services import orders as orders_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderList)
def list_my_orders(
    user: CurrentUser,
    conn: DbConn,
    status: OrderStatus | None = None,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return orders_service.list_buyer_orders(conn, user, status, page, limit)


@router.get("/{order_id}", response_model=OrderDetail)
def read_order(order_id: int, user: CurrentUser, conn: DbConn):
    return orders_service.get_order(conn, user, order_id)


@router.patch("/{order_id}", response_model=OrderDetail)
def update_order_status(
    order_id: int, payload: OrderStatusUpdate, user: CurrentUser, conn: DbConn
):
    return orders_service.change_status(conn, user, order_id, payload.status)
