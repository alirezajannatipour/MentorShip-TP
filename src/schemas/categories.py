from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str
    parent_id: int | None
