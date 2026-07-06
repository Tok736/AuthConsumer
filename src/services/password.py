"""Password hashing.

Uses passlib's ``bcrypt_sha256`` scheme rather than plain ``bcrypt``: it
pre-hashes with SHA-256 so passwords longer than bcrypt's 72-byte limit are
not silently truncated. The stored hash is still bcrypt under the hood.
"""

from functools import lru_cache

from passlib.context import CryptContext


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
    return PasswordHasher(get_settings().bcrypt_rounds)
