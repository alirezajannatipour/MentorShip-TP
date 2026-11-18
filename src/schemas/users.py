from datetime import datetime

from pydantic import BaseModel


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str


class UserMe(UserPublic):
    wallet_balance: int
    created_at: datetime


class RegisterResponse(BaseModel):
    user: UserPublic
    token: str
