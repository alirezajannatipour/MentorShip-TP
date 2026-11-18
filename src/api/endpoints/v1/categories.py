from fastapi import APIRouter

from src.api.dependencies import DbConn
from src.schemas.categories import CategoryOut
from src.services import categories as categories_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def read_categories(conn: DbConn):
    return categories_service.list_categories(conn)
