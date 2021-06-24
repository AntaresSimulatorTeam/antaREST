import io
import json
from glob import escape
from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, File, Depends, Body, Request
from fastapi.params import Param
from starlette.responses import StreamingResponse, Response

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.common.jwt import JWTUser
from antarest.common.requests import (
    RequestParameters,
)
from antarest.common.swagger import get_path_examples
from antarest.common.utils.web import APITag
from antarest.login.auth import Auth
from antarest.storage.model import (
    PublicMode,
    StudyDownloadDTO,
    StudyMetadataPatchDTO,
)
from antarest.common.config import Config
from antarest.storage.business.study_download_utils import StudyDownloader
from antarest.storage.service import StorageService


def sanitize_uuid(uuid: str) -> str:
    return str(escape(uuid))


def sanitize_study_name(name: str) -> str:
    return sanitize_uuid(name)


def create_study_routes(
    storage_service: StorageService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        storage_service: storage service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get("/studies", tags=[APITag.study_management], summary="Get Studies")
    def get_studies(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        available_studies = storage_service.get_studies_information(params)
        return available_studies

    @bp.post(
        "/studies/_import",
        status_code=HTTPStatus.CREATED.value,
        tags=[APITag.study_management],
        summary="Import Study",
    )
    def import_study(
        study: bytes = File(...),
        groups: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        zip_binary = io.BytesIO(study)

        params = RequestParameters(user=current_user)
        group_ids = groups.split(",") if groups is not None else []

        uuid = storage_service.import_study(zip_binary, group_ids, params)
        content = "/studies/" + uuid

        return content

    @bp.post(
        "/studies/{uuid}/copy",
        status_code=HTTPStatus.CREATED.value,
        tags=[APITag.study_management],
        summary="Copy Study",
    )
    def copy_study(
        uuid: str,
        dest: str,
        groups: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        source_uuid = uuid
        group_ids = groups.split(",") if groups is not None else []
        source_uuid_sanitized = sanitize_uuid(source_uuid)
        destination_name_sanitized = sanitize_study_name(dest)

        params = RequestParameters(user=current_user)

        destination_uuid = storage_service.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
            group_ids=group_ids,
            params=params,
        )

        return f"/studies/{destination_uuid}"

    @bp.post(
        "/studies",
        status_code=HTTPStatus.CREATED.value,
        tags=[APITag.study_management],
        summary="Create a new empty study",
    )
    def create_study(
        name: str,
        groups: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        name_sanitized = sanitize_study_name(name)
        group_ids = groups.split(",") if groups is not None else []
        group_ids = [sanitize_uuid(gid) for gid in group_ids]

        params = RequestParameters(user=current_user)
        uuid = storage_service.create_study(name_sanitized, group_ids, params)

        content = "/studies/" + uuid

        return content

    @bp.get(
        "/studies/{uuid}/export",
        tags=[APITag.study_management],
        summary="Export Study",
    )
    def export_study(
        uuid: str,
        no_output: Optional[bool] = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=current_user)
        content = storage_service.export_study(
            uuid_sanitized, params, not no_output
        )

        return StreamingResponse(
            content,
            headers={
                "Content-Disposition": f'attachment; filename="{uuid_sanitized}.zip'
            },
            media_type="application/zip",
        )

    @bp.delete(
        "/studies/{uuid}",
        status_code=HTTPStatus.OK.value,
        tags=[APITag.study_management],
        summary="Delete Study",
    )
    def delete_study(
        uuid: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=current_user)
        storage_service.delete_study(uuid_sanitized, params)

        return ""

    @bp.post(
        "/studies/{uuid}/output",
        status_code=HTTPStatus.ACCEPTED.value,
        tags=[APITag.study_outputs],
        summary="Import Output",
    )
    def import_output(
        uuid: str,
        output: bytes = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)

        zip_binary = io.BytesIO(output)

        params = RequestParameters(user=current_user)
        content = str(
            storage_service.import_output(uuid_sanitized, zip_binary, params)
        )

        return content

    @bp.put(
        "/studies/{uuid}/owner/{user_id}",
        tags=[APITag.study_permissions],
        summary="Change study owner",
    )
    def change_owner(
        uuid: str,
        user_id: int,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        storage_service.change_owner(uuid_sanitized, user_id, params)

        return ""

    @bp.put(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Add a group association",
    )
    def add_group(
        uuid: str,
        group_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_uuid(group_id)
        params = RequestParameters(user=current_user)
        storage_service.add_group(uuid_sanitized, group_id, params)

        return ""

    @bp.delete(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Remove a group association",
    )
    def remove_group(
        uuid: str,
        group_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_uuid(group_id)

        params = RequestParameters(user=current_user)
        storage_service.remove_group(uuid_sanitized, group_id, params)

        return ""

    @bp.put(
        "/studies/{uuid}/public_mode/{mode}",
        tags=[APITag.study_permissions],
        summary="Set study public mode",
    )
    def set_public_mode(
        uuid: str,
        mode: PublicMode,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        storage_service.set_public_mode(uuid_sanitized, mode, params)

        return ""

    @bp.get(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Get Study informations",
    )
    def get_study_metadata(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        study_metadata = storage_service.get_study_information(uuid, params)
        return study_metadata

    @bp.put(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Get Study informations",
    )
    def update_study_metadata(
        uuid: str,
        study_metadata_patch: StudyMetadataPatchDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        study_metadata = storage_service.update_study_information(
            uuid, study_metadata_patch, params
        )
        return study_metadata

    @bp.get(
        "/studies/{uuid}/raw",
        tags=[APITag.study_data],
        summary="Read data",
    )
    def get_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        depth: int = 3,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        parameters = RequestParameters(user=current_user)
        output = storage_service.get(uuid, path, depth, parameters)

        json_response = json.dumps(
            output,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
        return Response(content=json_response, media_type="application/json")

    @bp.post(
        "/studies/{uuid}/raw",
        status_code=HTTPStatus.NO_CONTENT.value,
        tags=[APITag.study_data],
        summary="Update data",
    )
    def edit_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        data: JSON = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        new = data
        if not new:
            raise HTTPException(
                status_code=400, detail="empty body not authorized"
            )

        path = sanitize_uuid(path)
        params = RequestParameters(user=current_user)
        storage_service.edit_study(uuid, path, new, params)
        content = ""

        return content

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
        responses={
            200: {
                "content": {
                    "application/json": {},
                    "application/zip": {},
                    "application/tar+gz": {},
                },
            },
        },
    )
    def output_download(
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        request: Request,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        params = RequestParameters(user=current_user)
        content = storage_service.download_outputs(
            study_id, output_id, data, params
        )
        accept = request.headers.get("Accept")
        if accept == "application/zip" or accept == "application/tar+gz":
            return StreamingResponse(
                StudyDownloader.export(content, accept),
                headers={
                    "Content-Disposition": f'attachment; filename="output-{output_id}.zip'
                },
                media_type="application/zip",
            )
        return content

    @bp.get(
        "/studies/{study_id}/outputs",
        summary="Get global information about a study simulation result",
        tags=[APITag.study_outputs],
    )
    def sim_result(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        content = storage_service.get_study_sim_result(study_id, params)
        return content

    @bp.put(
        "/studies/{study_id}/outputs/{output_id}/reference",
        summary="Set simulation as the reference output",
        tags=[APITag.study_outputs],
    )
    def set_sim_reference(
        study_id: str,
        output_id: str,
        status: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        params = RequestParameters(user=current_user)
        storage_service.set_sim_reference(study_id, output_id, status, params)
        return "OK"

    @bp.get(
        "/studies/{uuid}/validate",
        summary="Launch test validation on study",
        tags=[APITag.study_data],
    )
    def validate(uuid: str) -> Any:
        return storage_service.check_errors(uuid)

    return bp
