from faststream import FastStream

from src.rabbit import broker
from src.routers.auth import router

broker.include_router(router)

app = FastStream(broker)
