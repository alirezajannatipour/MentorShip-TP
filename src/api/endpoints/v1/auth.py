from fastapi import APIRouter

from src.api.dependencies import DbConn
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from src.schemas.users import RegisterResponse
from src.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=RegisterResponse)
def register(payload: RegisterRequest, conn: DbConn):
    return auth_service.register_user(conn, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, conn: DbConn):
    return auth_service.login(conn, payload)
