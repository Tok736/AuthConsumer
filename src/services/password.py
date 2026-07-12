from functools import lru_cache

from passlib.context import CryptContext

from src.config import settings


class PasswordHasher:
    def __init__(self, rounds: int):
        self._ctx = CryptContext(
            schemes=["bcrypt_sha256"],
            deprecated="auto",
            bcrypt_sha256__rounds=rounds,
        )

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._ctx.verify(password, hashed)


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return PasswordHasher(settings.auth.bcrypt_rounds)
