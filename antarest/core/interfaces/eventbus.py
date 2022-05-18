from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Optional, List, Awaitable

from pydantic import BaseModel

from antarest.core.model import PermissionInfo


class EventType(str, Enum):
    ANY = "_ANY"
    STUDY_CREATED = "STUDY_CREATED"
    STUDY_DELETED = "STUDY_DELETED"
    STUDY_EDITED = "STUDY_EDITED"
    STUDY_DATA_EDITED = "STUDY_DATA_EDITED"
    STUDY_JOB_STARTED = "STUDY_JOB_STARTED"
    STUDY_JOB_LOG_UPDATE = "STUDY_JOB_LOG_UPDATE"
    STUDY_JOB_COMPLETED = "STUDY_JOB_COMPLETED"
    STUDY_JOB_STATUS_UPDATE = "STUDY_JOB_STATUS_UPDATE"
    STUDY_JOB_CANCEL_REQUEST = "STUDY_JOB_CANCEL_REQUEST"
    STUDY_JOB_CANCELLED = "STUDY_JOB_CANCELLED"
    STUDY_VARIANT_GENERATION_COMMAND_RESULT = (
        "STUDY_VARIANT_GENERATION_COMMAND_RESULT"
    )
    TASK_ADDED = "TASK_ADDED"
    TASK_RUNNING = "TASK_RUNNING"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCEL_REQUEST = "TASK_CANCEL_REQUEST"
    DOWNLOAD_CREATED = "DOWNLOAD_CREATED"
    DOWNLOAD_READY = "DOWNLOAD_READY"
    DOWNLOAD_EXPIRED = "DOWNLOAD_EXPIRED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    MESSAGE_INFO = "MESSAGE_INFO"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    WORKER_TASK = "WORKER_TASK"
    WORKER_TASK_STARTED = "WORKER_TASK_STARTED"
    WORKER_TASK_ENDED = "WORKER_TASK_ENDED"


class EventChannelDirectory:
    JOB_STATUS = "JOB_STATUS/"
    JOB_LOGS = "JOB_LOGS/"
    TASK = "TASK/"
    STUDY_GENERATION = "GENERATION_TASK/"


class Event(BaseModel):
    type: EventType
    payload: Any
    permissions: PermissionInfo = PermissionInfo()
    channel: Optional[str] = None


class IEventBus(ABC):
    @abstractmethod
    def push(self, event: Event) -> None:
        pass

    @abstractmethod
    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[EventType]] = None,
    ) -> str:
        """
        Add an event listener listener
        @param listener listener callback
        @param type_filter list of event types to listen to (or None to catch all)

        Beware of the fact that in gunicorn, listeners will be called on the same event as many as there is workers
        """
        pass

    @abstractmethod
    def remove_listener(self, listener_id: str) -> None:
        pass

    @abstractmethod
    def start(self, threaded: bool = True) -> None:
        pass


class DummyEventBusService(IEventBus):
    def push(self, event: Event) -> None:
        # Noop
        pass

    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[EventType]] = None,
    ) -> str:
        return ""

    def remove_listener(self, listener_id: str) -> None:
        # Noop
        pass

    def start(self, threaded: bool = True) -> None:
        # Noop
        pass
