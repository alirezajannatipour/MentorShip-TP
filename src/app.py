from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.endpoints.v1 import router as v1_router
from src.connections.postgresql import close_pool, open_pool
from src.errors import AppError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    open_pool()
    yield
    close_pool()


app = FastAPI(
    title="E-commerce API",
    description="Multi-vendor e-commerce API (FastAPI + PostgreSQL)",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(v1_router, prefix="/v1")


def _error_response(status_code: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, **extra}},
    )


@app.exception_handler(AppError)
async def handle_app_error(_request: Request, exc: AppError):
    extra = {"details": exc.details} if exc.details else {}
    return _error_response(exc.status_code, exc.code, exc.message, **extra)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError):
    return _error_response(
        422,
        "VALIDATION_ERROR",
        "ورودی نامعتبر است.",
        details=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(_request: Request, exc: StarletteHTTPException):
    code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
        exc.status_code, f"HTTP_{exc.status_code}"
    )
    return _error_response(exc.status_code, code, str(exc.detail))
