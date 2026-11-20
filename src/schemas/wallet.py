from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.common import Pagination


class WalletOut(BaseModel):
    wallet_balance: int


class TransactionCreate(BaseModel):
    type: Literal["deposit"]
    amount: int = Field(gt=0, le=10_000_000_000)


class TransactionCreated(BaseModel):
    transaction_id: int
    type: str
    amount: int
    balance_after: int


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: int
    balance_after: int
    checkout_id: int | None
    order_id: int | None
    created_at: datetime


class TransactionList(BaseModel):
    items: list[TransactionOut]
    pagination: Pagination
