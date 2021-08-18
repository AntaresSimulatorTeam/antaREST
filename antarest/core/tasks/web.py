import logging
from typing import Any

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskListFilter
from antarest.core.tasks.service import TaskJobService
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def create_tasks_api(service: TaskJobService, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        config: server config
        jwt: jwt manager

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get("/tasks")
    def list_tasks(
        filter: TaskListFilter,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.list_tasks(filter, request_params)

    return bp
