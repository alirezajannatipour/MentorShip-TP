from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from src.schemas.common import Pagination

ImageUrl = Annotated[str, StringConstraints(max_length=500, pattern=r"^https?://")]


class ProductCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    shop_id: int
    category_id: int
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    price: int = Field(ge=0, le=1_000_000_000_000)
    stock: int = Field(ge=0, le=1_000_000)
    images: list[ImageUrl] = Field(default_factory=list, max_length=10)


class ProductImage(BaseModel):
    url: str
    sort_order: int


class CategoryRef(BaseModel):
    id: int
    name: str


class ShopRef(BaseModel):
    id: int
    name: str
    logo_url: str | None


class ProductDetail(BaseModel):
    id: int
    title: str
    description: str | None
    price: int
    stock: int
    sold_count: int
    created_at: datetime
    images: list[ProductImage]
    category: CategoryRef
    shop: ShopRef


class ProductListItem(BaseModel):
    id: int
    title: str
    price: int
    in_stock: bool
    main_image_url: str | None
    shop_name: str
    category_name: str


class ProductList(BaseModel):
    items: list[ProductListItem]
    pagination: Pagination
