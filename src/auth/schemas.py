"""Request bodies and response `data` payloads for the auth endpoints."""

from typing import Any

from pydantic import BaseModel, EmailStr, Field


# fmt: off
class RegisterRequest(BaseModel):
    email:           EmailStr
    password:        str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email:           EmailStr
    password:        str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token:   str


class RevokeRequest(BaseModel):
    refresh_token:   str
    all_sessions:    bool = False


class UserData(BaseModel):
    id:              str
    email:           str
    is_active:       bool


class TokenPair(BaseModel):
    access_token:    str
    refresh_token:   str
    token_type:      str = "Bearer"
    expires_in:      int


class Response(BaseModel):
    status: int = 200
    message: str = "Ok"
    data: Any | None = None


def ok(data: Any = None, status: int = 200, message: str = "Ok") -> Response:
    return Response(status=status, message=message, data=data)


def err(status: int, message: str) -> Response:
    return Response(status=status, message=message, data=None)


# fmt: on
