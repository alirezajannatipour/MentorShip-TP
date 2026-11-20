from fastapi import APIRouter, Response

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.cart import CartItemCreate, CartItemOut, CartItemUpdate, CartOut
from src.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartOut)
def read_cart(user: CurrentUser, conn: DbConn):
    return cart_service.get_cart(conn, user)


@router.post("/items", status_code=201, response_model=CartItemOut)
def add_cart_item(
    payload: CartItemCreate, user: CurrentUser, conn: DbConn, response: Response
):
    item, created = cart_service.add_item(
        conn, user, payload.product_id, payload.quantity
    )
    if not created:
        # محصول از قبل در سبد بود و تعدادش جمع شد
        response.status_code = 200
    return item


@router.patch("/items/{item_id}", response_model=CartItemOut)
def update_cart_item(
    item_id: int, payload: CartItemUpdate, user: CurrentUser, conn: DbConn
):
    return cart_service.update_item(conn, user, item_id, payload.quantity)


@router.delete("/items/{item_id}", status_code=204)
def delete_cart_item(item_id: int, user: CurrentUser, conn: DbConn):
    cart_service.delete_item(conn, user, item_id)
    return Response(status_code=204)
