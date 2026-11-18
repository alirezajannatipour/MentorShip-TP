from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.]+$")
    email: EmailStr
    phone_number: str = Field(pattern=r"^09\d{9}$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr | None = None
    username: str | None = None
    password: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def exactly_one_identifier(self):
        if (self.email is None) == (self.username is None):
            raise ValueError("Provide exactly one of email or username")
        return self


class TokenResponse(BaseModel):
    token: str
