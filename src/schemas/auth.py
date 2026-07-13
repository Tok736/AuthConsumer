from pydantic import BaseModel, EmailStr, Field, SecretStr

from src.enums import BasicRole


# fmt: off
class RegisterRequest(BaseModel):
    email:           EmailStr
    password:        SecretStr = Field(min_length=8, max_length=128)
    nickname:        str
    basic_role:      BasicRole


class LoginRequest(BaseModel):
    email:           EmailStr
    password:        SecretStr = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token:   str


class RevokeRequest(BaseModel):
    refresh_token:   str
    all_sessions:    bool = False


class UserRead(BaseModel):
    id:              int
    email:           str
    is_active:       bool


class TokenPair(BaseModel):
    access_token:    str
    refresh_token:   str
    token_type:      str = "Bearer"
    expires_at:      int


# fmt: on
