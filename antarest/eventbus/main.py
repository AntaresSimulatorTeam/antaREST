from typing import Optional

from fastapi import FastAPI
from redis import Redis

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.business.redis_eventbus import RedisEventBus
from antarest.eventbus.service import EventBusService
from antarest.eventbus.web import configure_websockets


def build_eventbus(
    application: FastAPI,
    config: Config,
    autostart: bool = True,
    redis_client: Optional[Redis] = None,  # type: ignore
) -> IEventBus:

    eventbus = EventBusService(
        RedisEventBus(redis_client)
        if redis_client is not None
        else LocalEventBus(),
        autostart,
    )

    configure_websockets(application, config, eventbus)
    return eventbus
