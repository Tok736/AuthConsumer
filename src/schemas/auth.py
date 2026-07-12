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


class UserRead(BaseModel):
    id:              int
    email:           str
    is_active:       bool


class TokenPair(BaseModel):
    access_token:    str
    refresh_token:   str
    token_type:      str = "Bearer"
    expires_in:      int


# fmt: on
