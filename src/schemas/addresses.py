from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    province: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address_detail: str = Field(min_length=1, max_length=1000)
    postal_code: str | None = Field(default=None, pattern=r"^\d{10}$")


class AddressOut(BaseModel):
    id: int
    province: str
    city: str
    address_detail: str
    postal_code: str | None
