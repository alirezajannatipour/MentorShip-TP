from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShopCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    logo_url: str | None = Field(default=None, max_length=500, pattern=r"^https?://")


class ShopOut(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str | None
    logo_url: str | None
    created_at: datetime


class ShopPublic(BaseModel):
    id: int
    name: str
    description: str | None
    logo_url: str | None
    created_at: datetime
