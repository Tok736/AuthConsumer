from collections.abc import AsyncGenerator
from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker


class BaseRepository:
    """
    Класс для работы с базой данных. Синтаксис использования:

    ```
    async with Repository() as db:
        patterns = await db.get_patterns()
    ```

    """

    session: AsyncSession

    def __init__(self, session: AsyncSession | None = None) -> None:
        if session is None:
            self.session = async_session_maker()  # type: ignore
        else:
            self.session = session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.session.close()

    @classmethod
    async def dependency(cls) -> AsyncGenerator[Self]:
        """
        Функция для использования с Depends. Синтаксис использования:

        ```
        @router.get("")
        async def get(db: Repository = Depends(Repository.dependency)):
            ...
        ```
        """

        async with cls() as db:
            yield db
