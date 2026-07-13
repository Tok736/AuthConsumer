from faststream import Depends
from faststream.rabbit import RabbitRouter

from src.base_schemas import Response
from src.config import settings
from src.rabbit import queue
from src.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, RevokeRequest, TokenPair
from src.services.auth import AuthService
from src.services.token import TokenService

from .dependencies import get_auth_service, get_token_service

router = RabbitRouter()


@router.subscriber(queue.post("register"))
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response[TokenPair]:
    return await service.register(request)


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
) -> Response:
    return await service.refresh(request)


@router.subscriber(queue.post("revoke"))
async def revoke(
    request: RevokeRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    return await service.revoke(request)


@router.subscriber(queue.get("jwks"))
async def jwks(tokens: TokenService = Depends(get_token_service)) -> Response:
    return Response(data=tokens.jwks())


@router.subscriber(queue.get("public_key"))
async def public_key(
    tokens: TokenService = Depends(get_token_service),
) -> Response:
    return Response(
        data={
            "public_key": tokens.public_key_pem,
            "algorithm": settings.auth.jwt_algorithm,
            "kid": tokens.kid,
        }
    )
