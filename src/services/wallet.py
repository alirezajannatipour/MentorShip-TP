from typing import Any

import psycopg

from src.repositories import wallet as wallet_repo
from src.schemas.wallet import TransactionCreate
from src.services import idempotency
from src.utils.pagination import build_pagination


def get_wallet(conn: psycopg.Connection, user: dict[str, Any]) -> dict[str, int]:
    return {"wallet_balance": wallet_repo.get_balance(conn, user["id"])}


def list_transactions(
    conn: psycopg.Connection, user: dict[str, Any], page: int, limit: int
) -> dict[str, Any]:
    total = wallet_repo.count_transactions(conn, user["id"])
    items = wallet_repo.list_transactions(conn, user["id"], limit, (page - 1) * limit)
    return {"items": items, "pagination": build_pagination(total, page, limit)}


def deposit(
    conn: psycopg.Connection,
    user: dict[str, Any],
    idempotency_key: str,
    data: TransactionCreate,
) -> tuple[int, dict[str, Any]]:
    def handler() -> tuple[int, dict[str, Any]]:
        balance_after = wallet_repo.credit(conn, user["id"], data.amount)
        tx = wallet_repo.insert_transaction(
            conn,
            user_id=user["id"],
            amount=data.amount,
            type_="deposit",
            balance_after=balance_after,
        )
        return 201, {
            "transaction_id": tx["id"],
            "type": "deposit",
            "amount": data.amount,
            "balance_after": balance_after,
        }

    return idempotency.run_idempotent(
        conn,
        user_id=user["id"],
        key=idempotency_key,
        scope="wallet_deposit",
        payload=data.model_dump(mode="json"),
        handler=handler,
    )
