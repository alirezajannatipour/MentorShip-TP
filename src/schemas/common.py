from pydantic import BaseModel


class Pagination(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
