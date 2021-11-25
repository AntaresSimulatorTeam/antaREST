from abc import ABC, abstractmethod
from typing import Callable, NamedTuple, Optional, Any
from uuid import UUID

from antarest.core.config import Config
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.launcher.model import JobStatus, LogType
from antarest.study.service import StudyService


class LauncherInitException(Exception):
    pass


class LauncherCallbacks(NamedTuple):
    update_status: Callable[
        [str, JobStatus, Optional[str], Optional[str]], None
    ]


class AbstractLauncher(ABC):
    def __init__(
        self,
        config: Config,
        storage_service: StudyService,
        callbacks: LauncherCallbacks,
    ):
        self.config = config
        self.storage_service = storage_service
        self.callbacks = callbacks

    @abstractmethod
    def run_study(
        self,
        study_uuid: str,
        version: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> UUID:
        raise NotImplementedError()

    @abstractmethod
    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def kill_job(self, job_id: str) -> None:
        raise NotImplementedError()
