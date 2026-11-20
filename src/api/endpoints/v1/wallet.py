from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.api.dependencies import CurrentUser, DbConn, IdempotencyKey
from src.schemas.wallet import (
    TransactionCreate,
    TransactionCreated,
    TransactionList,
    WalletOut,
)
from src.services import wallet as wallet_service

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletOut)
def read_wallet(user: CurrentUser, conn: DbConn):
    return wallet_service.get_wallet(conn, user)


@router.get("/transactions", response_model=TransactionList)
def read_transactions(
    user: CurrentUser,
    conn: DbConn,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return wallet_service.list_transactions(conn, user, page, limit)


@router.post("/transactions", status_code=201, response_model=TransactionCreated)
def create_transaction(
    payload: TransactionCreate,
    user: CurrentUser,
    idempotency_key: IdempotencyKey,
    conn: DbConn,
):
    status, body = wallet_service.deposit(conn, user, idempotency_key, payload)
    return JSONResponse(content=body, status_code=status)
