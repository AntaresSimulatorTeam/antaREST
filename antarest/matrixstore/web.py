from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Body, Query, File, UploadFile

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    UserHasNotPermissionError,
    RequestParameters,
)
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixDataSetUpdateDTO,
    MatrixInfoDTO,
)
from antarest.matrixstore.service import MatrixService


def create_matrix_api(service: MatrixService, config: Config) -> APIRouter:
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

    @bp.post("/matrix", tags=[APITag.matrix])
    def create(
        matrix: MatrixDTO = Body(description="matrix dto", default={}),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        if current_user.id is not None:
            return service.create(matrix)
        raise UserHasNotPermissionError()

    @bp.post("/matrix/_import", tags=[APITag.matrix])
    def create_by_importation(
        file: UploadFile = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        if current_user.id is not None:
            return service.create_by_importation(file)
        raise UserHasNotPermissionError()

    @bp.get("/matrix/{id}", tags=[APITag.matrix])
    def get(id: str, user: JWTUser = Depends(auth.get_current_user)) -> Any:
        if user.id is not None:
            return service.get(id)
        raise UserHasNotPermissionError()

    @bp.post("/matrixdataset", tags=[APITag.matrix])
    def create_dataset(
        metadata: MatrixDataSetUpdateDTO = Body(...),
        matrices: List[MatrixInfoDTO] = Body(...),
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=user)
        return service.create_dataset(
            metadata, matrices, request_params
        ).to_dto()

    @bp.put("/matrixdataset/{id}/metadata", tags=[APITag.matrix])
    def update_dataset_metadata(
        id: str,
        metadata: MatrixDataSetUpdateDTO,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=user)
        return service.update_dataset(id, metadata, request_params).to_dto()

    @bp.get("/matrixdataset/_search", tags=[APITag.matrix])
    def query_datasets(
        name: Optional[str],
        filter_own: bool = False,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=user)
        return service.list(name, filter_own, request_params)

    @bp.delete("/matrixdataset/{id}", tags=[APITag.matrix])
    def delete_datasets(
        id: str,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=user)
        service.delete_dataset(id, request_params)

    return bp
