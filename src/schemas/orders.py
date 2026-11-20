from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.schemas.common import Pagination

OrderStatus = Literal["pending", "paid", "shipping", "delivered", "cancelled"]


class OrderStatusUpdate(BaseModel):
    status: Literal["shipping", "delivered", "cancelled"]


class OrderItemOut(BaseModel):
    product_id: int
    title: str
    quantity: int
    price_at_purchase: int


class ReceiverFields(BaseModel):
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    address_detail: str
    postal_code: str | None


class OrderListItem(BaseModel):
    order_id: int
    checkout_id: int
    shop_id: int
    shop_name: str
    total_price: int
    status: str
    created_at: datetime


class OrderList(BaseModel):
    items: list[OrderListItem]
    pagination: Pagination


class OrderDetail(ReceiverFields):
    order_id: int
    checkout_id: int
    shop_id: int
    total_price: int
    status: str
    created_at: datetime
    items: list[OrderItemOut]


class ShopOrder(ReceiverFields):
    order_id: int
    status: str
    total_price: int
    created_at: datetime
    items: list[OrderItemOut]


class ShopOrderList(BaseModel):
    items: list[ShopOrder]
    pagination: Pagination
