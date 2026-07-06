from faststream.rabbit import RabbitBroker, RabbitQueue

from src.config import settings
from src.logger import logger

broker = RabbitBroker(settings.rabbit.rabbit_url, logger=logger)


def create_queue(prefix: str, method: str, path: str) -> RabbitQueue:
    return RabbitQueue(
        name=f"{prefix}.{method}.{path}",
        durable=True,
        arguments={"x-message-ttl": settings.rabbit.message_ttl},
    )


class queue:
    """Класс для создания RestAPI-подобных очередей"""

    prefix = "auth_service"

    @staticmethod
    def get(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "get", path)

    @staticmethod
    def post(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "post", path)

    @staticmethod
    def put(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "put", path)

    @staticmethod
    def delete(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "delete", path)
