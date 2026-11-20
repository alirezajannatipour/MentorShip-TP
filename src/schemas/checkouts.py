from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckoutCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    address_id: int
    receiver_name: str = Field(min_length=1, max_length=100)
    receiver_phone: str = Field(pattern=r"^09\d{9}$")
    expected_total_price: int = Field(ge=0)


class OrderSummary(BaseModel):
    order_id: int
    shop_id: int
    total_price: int
    status: str


class CheckoutCreated(BaseModel):
    checkout_id: int
    total_price: int
    wallet_balance_after: int
    orders: list[OrderSummary]


class CheckoutDetail(BaseModel):
    checkout_id: int
    total_price: int
    payment_method: str
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    address_detail: str
    postal_code: str | None
    created_at: datetime
    orders: list[OrderSummary]
