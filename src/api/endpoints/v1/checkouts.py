from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.api.dependencies import CurrentUser, DbConn, IdempotencyKey
from src.schemas.checkouts import CheckoutCreate, CheckoutCreated, CheckoutDetail
from src.services import checkouts as checkouts_service

router = APIRouter(prefix="/checkouts", tags=["checkouts"])


@router.post("", status_code=201, response_model=CheckoutCreated)
def create_checkout(
    payload: CheckoutCreate,
    user: CurrentUser,
    idempotency_key: IdempotencyKey,
    conn: DbConn,
):
    status, body = checkouts_service.create_checkout(
        conn, user, idempotency_key, payload
    )
    return JSONResponse(content=body, status_code=status)


@router.get("/{checkout_id}", response_model=CheckoutDetail)
def read_checkout(checkout_id: int, user: CurrentUser, conn: DbConn):
    return checkouts_service.get_checkout(conn, user, checkout_id)
