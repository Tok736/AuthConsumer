import base64
import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization

from src.config import settings
from src.exceptions import InvalidToken


def b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


class TokenService:
    def __init__(self):
        with open("/edcurve/secrets/rsa/private.pem", "rb") as fh:
            self._private_key = serialization.load_pem_private_key(fh.read(), password=None)
        self._public_key = self._private_key.public_key()

        public_der = self._public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.kid = base64.urlsafe_b64encode(hashlib.sha256(public_der).digest()).decode().rstrip("=")[:16]
        self.public_pem = self._public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    @property
    def public_key_pem(self) -> str:
        return self.public_pem

    def jwks(self) -> dict:
        numbers = self._public_key.public_numbers()
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": settings.auth.jwt_algorithm,
                    "kid": self.kid,
                    "n": b64url_uint(numbers.n),
                    "e": b64url_uint(numbers.e),
                }
            ]
        }

    def create_access_token(self, user_id: int) -> tuple[str, int]:
        now = datetime.now(UTC)
        exp = now + timedelta(seconds=settings.auth.access_token_ttl)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iss": settings.auth.jwt_issuer,
            "aud": settings.auth.jwt_audience,
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
        }
        token = jwt.encode(
            payload,
            self._private_key,
            algorithm=settings.auth.jwt_algorithm,
            headers={"kid": self.kid},
        )
        expired_at = int(exp.timestamp())
        return token, expired_at

    def create_refresh_token(self, user_id: int, family_id: uuid.UUID) -> tuple[str, uuid.UUID, datetime]:
        ttl = settings.auth.refresh_token_ttl
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl)
        jti = uuid.uuid4()
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
            self._private_key,
            algorithm=settings.auth.jwt_algorithm,
            headers={"kid": self.kid},
        )
        return token, jti, expires_at

    def decode_refresh(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self._public_key,
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
