import time
from datetime import datetime, timedelta
from typing import Callable
from unittest.mock import Mock, MagicMock

from antarest.core.config import Config, EventBusConfig, RedisConfig
from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.main import build_eventbus


def autoretry(func: Callable[..., bool], timeout: int) -> None:
    threshold = datetime.utcnow() + timedelta(seconds=timeout)
    while datetime.utcnow() < threshold:
        if func():
            return
        time.sleep(0.2)
    raise AssertionError()


def test_service_factory():
    config = Config()
    redis_client = Mock()
    event_bus = build_eventbus(MagicMock(), config, autostart=False)
    assert event_bus.backend.__class__.__name__ == "LocalEventBus"
    config = Config(
        redis=RedisConfig(host="localhost"), eventbus=EventBusConfig()
    )

    event_bus = build_eventbus(
        MagicMock(), config, autostart=False, redis_client=redis_client
    )
    assert event_bus.backend.__class__.__name__ == "RedisEventBus"


def test_lifecycle():
    event_bus = build_eventbus(MagicMock(), Config(), autostart=True)
    test_bucket = []
    lid = event_bus.add_listener(lambda event: test_bucket.append(event))
    event = Event("test", "foo")
    event_bus.push(event)
    autoretry(lambda: len(test_bucket) == 1, 2)

    event_bus.remove_listener(lid)
    test_bucket.clear()
    event_bus.push(event)
    autoretry(lambda: len(test_bucket) == 0, 2)
