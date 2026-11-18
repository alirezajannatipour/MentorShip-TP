from fastapi import APIRouter

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.shops import ShopCreate, ShopOut, ShopPublic
from src.services import shops as shops_service

router = APIRouter(prefix="/shops", tags=["shops"])


@router.post("", status_code=201, response_model=ShopOut)
def create_shop(payload: ShopCreate, user: CurrentUser, conn: DbConn):
    return shops_service.create_shop(conn, user, payload)


@router.get("/{shop_id}", response_model=ShopPublic)
def read_shop(shop_id: int, conn: DbConn):
    return shops_service.get_shop(conn, shop_id)
