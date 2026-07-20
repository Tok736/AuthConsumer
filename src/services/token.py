import base64
import hashlib
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from uuid import UUID, uuid7

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from src.config import settings
from src.exceptions import InvalidToken
from src.schemas.auth import JWK, JWKS


def b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


class TokenService:
    def __init__(self):
        with open("/edcurve/secrets/rsa/private.pem", "rb") as fh:
            self.private_key: RSAPrivateKey = serialization.load_pem_private_key(fh.read(), password=None)  # pyright: ignore[reportAttributeAccessIssue]
        self.public_key: RSAPublicKey = self.private_key.public_key()  # pyright: ignore[reportAttributeAccessIssue]

        public_der = self.public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.kid = base64.urlsafe_b64encode(hashlib.sha256(public_der).digest()).decode().rstrip("=")[:16]
        self.public_pem = self.public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    @property
    def public_key_pem(self) -> str:
        return self.public_pem

    def jwks(self) -> JWKS:
        numbers = self.public_key.public_numbers()
        return JWKS(
            keys=[
                JWK(
                    alg=settings.auth.jwt_algorithm,
                    kid=self.kid,
                    n=b64url_uint(numbers.n),
                    e=b64url_uint(numbers.e),
                )
            ]
        )

    def create_access_token(self, user_id: UUID) -> tuple[str, int]:
        now = datetime.now(UTC)
        exp = now + timedelta(seconds=settings.auth.access_token_ttl)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iss": settings.auth.jwt_issuer,
            "aud": settings.auth.jwt_audience,
            "iat": now,
            "exp": exp,
            "jti": str(uuid7()),
        }
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm=settings.auth.jwt_algorithm,
            headers={"kid": self.kid},
        )
        expired_at = int(exp.timestamp())
        return token, expired_at

    def create_refresh_token(self, user_id: UUID, family_id: UUID) -> tuple[str, UUID, datetime]:
        ttl = settings.auth.refresh_token_ttl
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl)
        jti = uuid7()
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(jti),
            "fid": str(family_id),
            "iss": settings.auth.jwt_issuer,
            "aud": settings.auth.jwt_audience,
            "iat": now,
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm=settings.auth.jwt_algorithm,
            headers={"kid": self.kid},
        )
        return token, jti, expires_at

    def decode_refresh(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[settings.auth.jwt_algorithm],
                audience=settings.auth.jwt_audience,
                issuer=settings.auth.jwt_issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc
        if payload.get("type") != "refresh":
            raise InvalidToken("Not a refresh token")
        return payload


@lru_cache
def get_token_service() -> TokenService:
    """Singleton: RSA ключи загружаются один раз"""
    return TokenService()
