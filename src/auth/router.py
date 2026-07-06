from faststream import Depends
from faststream.rabbit import RabbitMessage, RabbitRouter

from src.config import settings
from src.rabbit import queue
from src.services.auth import AuthService
from src.services.token import TokenService

from ..schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RevokeRequest,
)
from .dependencies import get_auth_service, get_token_service
from .schemas import Response, ok

router = RabbitRouter()


def _idem_key(msg: RabbitMessage) -> str | None:
    """Prefer an explicit Idempotency-Key header, fall back to correlation_id.

    The caller must reuse the same value across retries of one logical
    request for deduplication to work.
    """
    header = (msg.headers or {}).get("idempotency-key")
    return header or msg.correlation_id


# --- mutating endpoints (idempotent) --------------------------------------
@router.subscriber(queue.post("auth.register"))
async def register(
    request: RegisterRequest,
    msg: RabbitMessage,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    return await service.register(request, _idem_key(msg))


@router.subscriber(queue.post("auth.login"))
async def login(
    request: LoginRequest,
    msg: RabbitMessage,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    return await service.login(request, _idem_key(msg))


@router.subscriber(queue.post("auth.refresh"))
async def refresh(
    request: RefreshRequest,
    msg: RabbitMessage,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    return await service.refresh(request, _idem_key(msg))


@router.subscriber(queue.post("auth.revoke"))
async def revoke(
    request: RevokeRequest,
    msg: RabbitMessage,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    return await service.revoke(request, _idem_key(msg))


# --- read-only key endpoints (no DB, no idempotency) ----------------------
@router.subscriber(queue.get("auth.jwks"))
async def jwks(
    tokens: TokenService = Depends(get_token_service),
) -> Response:
    return ok(data=tokens.jwks())


@router.subscriber(queue.get("auth.public_key"))
async def public_key(
    tokens: TokenService = Depends(get_token_service),
) -> Response:
    return ok(
        data={
            "public_key": tokens.public_key_pem,
            "algorithm": settings.jwt_algorithm,
            "kid": tokens.kid,
        }
    )
