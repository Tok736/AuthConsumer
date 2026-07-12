from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

from src.config import settings
from src.logger import logger

broker = RabbitBroker(settings.rabbit.rabbit_url, logger=logger)
app = FastStream(broker)


def create_queue(prefix: str, method: str, path: str) -> RabbitQueue:
    name = f"{prefix}.{method}.{path}"
    logger.info(f"[create_queue] Creating queue with name {name}")
    return RabbitQueue(
        name=name,
        durable=True,
        arguments={"x-message-ttl": settings.rabbit.message_ttl},
    )


class queue:
    """Класс для создания RestAPI-подобных очередей"""

    prefix = "auth_consumer"

    @staticmethod
    def get(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "GET", path)

    @staticmethod
    def post(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "POST", path)

    @staticmethod
    def put(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "PUT", path)

    @staticmethod
    def delete(path: str) -> RabbitQueue:
        return create_queue(queue.prefix, "DELETE", path)
