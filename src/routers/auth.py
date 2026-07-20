from faststream import Context, Depends
from faststream.rabbit import RabbitRouter

from src.config import settings
from src.rabbit import Response, queue
from src.schemas.auth import (
    JWKS,
    LoginRequest,
    PublicKeyResponse,
    RefreshRequest,
    RegisterRequest,
    RevokeRequest,
    TokenPair,
)
from src.services import AuthService, TokenService

from .dependencies import get_auth_service, get_token_service

router = RabbitRouter()


@router.subscriber(queue.post("register"))
async def register(
    request: RegisterRequest,
    correlation_id: str = Context("message.correlation_id"),
    service: AuthService = Depends(get_auth_service),
) -> Response[TokenPair]:
    return await service.register(request, correlation_id)


@router.subscriber(queue.post("login"))
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response[TokenPair]:
    return await service.login(request)


@router.subscriber(queue.post("refresh"))
async def refresh(
    request: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response[TokenPair]:
    return await service.refresh(request)


@router.subscriber(queue.post("revoke"))
async def revoke(
    request: RevokeRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    return await service.revoke(request)


@router.subscriber(queue.get("jwks"))
async def jwks(tokens: TokenService = Depends(get_token_service)) -> Response[JWKS]:
    return Response(data=tokens.jwks())


@router.subscriber(queue.get("public_key"))
async def public_key(
    tokens: TokenService = Depends(get_token_service),
) -> Response[PublicKeyResponse]:
    return Response(
        data=PublicKeyResponse(
            public_key=tokens.public_key_pem,
            algorithm=settings.auth.jwt_algorithm,
            kid=tokens.kid,
        )
    )
