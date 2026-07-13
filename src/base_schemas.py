from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# fmt: off
class Response(BaseModel, Generic[T]):
    status:   int      = 200
    message:  str      = "Ok"
    data:     T | None = None
# fmt: on


def err(status: int, message: str) -> Response:
    return Response(status=status, message=message, data=None)
