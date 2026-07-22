from uuid import UUID

from pydantic import BaseModel

from src.enums import BasicRole
from src.exceptions import UserServiceUnavailable
from src.rabbit import Response, rpc_call


# fmt: off
class UserCreate(BaseModel):
    user_id:         UUID
    basic_role:      BasicRole
    email:           str
    nickname:        str
    timezone:        str
    locale:          str
# fmt: on


class ExternalUserService:
    """Класс для взаимодействия с микросервисом UserService"""

    async def create_user(self, user: UserCreate, correlation_id: str) -> Response:
        """Создать пользователя"""

        result = await rpc_call(
            user,
            "POST-user_service/user",
            Response,
            correlation_id=correlation_id,
            timeout=3,
        )

        if result is None:
            raise UserServiceUnavailable()

        return result
