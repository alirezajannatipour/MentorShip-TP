from fastapi import APIRouter

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.shops import ShopOut
from src.schemas.users import UserMe
from src.services import shops as shops_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
def read_me(user: CurrentUser):
    return user


@router.get("/me/shops", response_model=list[ShopOut])
def read_my_shops(user: CurrentUser, conn: DbConn):
    return shops_service.list_my_shops(conn, user)
