from fastapi import APIRouter

from src.api.endpoints.v1 import (
    addresses,
    auth,
    cart,
    categories,
    checkouts,
    orders,
    products,
    shops,
    users,
    wallet,
)

router = APIRouter()
for module in (
    auth,
    users,
    shops,
    categories,
    products,
    addresses,
    cart,
    wallet,
    checkouts,
    orders,
):
    router.include_router(module.router)
