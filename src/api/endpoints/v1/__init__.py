from fastapi import APIRouter

from src.api.endpoints.v1 import auth, categories, products, shops, users

router = APIRouter()
for module in (auth, users, shops, categories, products):
    router.include_router(module.router)
