from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=1000)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=1000)


class CartItemOut(BaseModel):
    item_id: int
    product_id: int
    quantity: int


class CartLine(BaseModel):
    item_id: int
    product_id: int
    product_title: str
    price: int
    quantity: int
    shop_id: int
    shop_name: str


class CartOut(BaseModel):
    cart_id: int | None
    items: list[CartLine]
    total_price: int
