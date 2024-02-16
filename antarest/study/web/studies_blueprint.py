import collections
import io
import logging
import typing as t
from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request
from markupsafe import escape
from pydantic import NonNegativeInt

from antarest.core.config import Config
from antarest.core.exceptions import BadZipBinary
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.utils.utils import BadArchiveContent, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import (
    CommentsDto,
    ExportFormat,
    MatrixIndex,
    StudyDownloadDTO,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
    StudySimResultDTO,
)
from antarest.study.repository import AccessPermissions, StudyFilter, StudyPagination, StudySortBy
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO

logger = logging.getLogger(__name__)


def _split_comma_separated_values(value: str, *, default: t.Sequence[str] = ()) -> t.Sequence[str]:
    """Split a comma-separated list of values into an ordered set of strings."""
    values = value.split(",") if value else default
    # drop whitespace around values
    values = [v.strip() for v in values]
    # remove duplicates and preserve order (to have a deterministic result for unit tests).
    return list(collections.OrderedDict.fromkeys(values))


def create_study_routes(study_service: StudyService, ftm: FileTransferManager, config: Config) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        study_service: study service facade to handle request
        ftm: file transfer manager
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies",
        tags=[APITag.study_management],
        summary="Get Studies",
    )
    def get_studies(
        current_user: JWTUser = Depends(auth.get_current_user),
        name: str = Query(
            "",
            description=(
                "Filter studies based on their name."
                "Case-insensitive search for studies whose name contains the specified value."
            ),
            alias="name",
        ),
        managed: t.Optional[bool] = Query(None, description="Filter studies based on their management status."),
        archived: t.Optional[bool] = Query(None, description="Filter studies based on their archive status."),
        variant: t.Optional[bool] = Query(None, description="Filter studies based on their variant status."),
        versions: str = Query(
            "",
            description="Comma-separated list of versions for filtering.",
            regex=r"^\s*(?:\d+\s*(?:,\s*\d+\s*)*)?$",
        ),
        users: str = Query(
            "",
            description="Comma-separated list of user IDs for filtering.",
            regex=r"^\s*(?:\d+\s*(?:,\s*\d+\s*)*)?$",
        ),
        groups: str = Query("", description="Comma-separated list of group IDs for filtering."),
        tags: str = Query("", description="Comma-separated list of tags for filtering."),
        study_ids: str = Query(
            "",
            description="Comma-separated list of study IDs for filtering.",
            alias="studyIds",
        ),
        exists: t.Optional[bool] = Query(None, description="Filter studies based on their existence on disk."),
        workspace: str = Query("", description="Filter studies based on their workspace."),
        folder: str = Query("", description="Filter studies based on their folder."),
        # It is advisable to use an optional Query parameter for enumerated types, like booleans.
        sort_by: t.Optional[StudySortBy] = Query(
            None,
            description="Sort studies based on their name (case-insensitive) or creation date.",
            alias="sortBy",
        ),
        page_nb: NonNegativeInt = Query(
            0,
            description="Page number (starting from 0).",
            alias="pageNb",
        ),
        page_size: NonNegativeInt = Query(
            0,
            description="Number of studies per page (0 = no limit).",
            alias="pageSize",
        ),
    ) -> t.Dict[str, StudyMetadataDTO]:
        """
        Get the list of studies matching the specified criteria.

        Args:
        - `name`: Filter studies based on their name. Case-insensitive search for studies
          whose name contains the specified value.
        - `managed`: Filter studies based on their management status.
        - `archived`: Filter studies based on their archive status.
        - `variant`: Filter studies based on their variant status.
        - `versions`: Comma-separated list of versions for filtering.
        - `users`: Comma-separated list of user IDs for filtering.
        - `groups`: Comma-separated list of group IDs for filtering.
        - `tags`: Comma-separated list of tags for filtering.
        - `studyIds`: Comma-separated list of study IDs for filtering.
        - `exists`: Filter studies based on their existence on disk.
        - `workspace`: Filter studies based on their workspace.
        - `folder`: Filter studies based on their folder.
        - `sortBy`: Sort studies based on their name (case-insensitive) or date.
        - `pageNb`: Page number (starting from 0).
        - `pageSize`: Number of studies per page (0 = no limit).

        Returns:
        - A dictionary of studies matching the specified criteria,
          where keys are study IDs and values are study properties.
        """

        logger.info("Fetching for matching studies", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)

        user_list = [int(v) for v in _split_comma_separated_values(users)]

        if not params.user:
            logger.error("FAIL permission: user is not logged")
            raise UserHasNotPermissionError()

        study_filter = StudyFilter(
            name=name,
            managed=managed,
            archived=archived,
            variant=variant,
            versions=_split_comma_separated_values(versions),
            users=user_list,
            groups=_split_comma_separated_values(groups),
            tags=_split_comma_separated_values(tags),
            study_ids=_split_comma_separated_values(study_ids),
            exists=exists,
            workspace=workspace,
            folder=folder,
            access_permissions=AccessPermissions.from_params(params),
        )

        matching_studies = study_service.get_studies_information(
            params=params,
            study_filter=study_filter,
            sort_by=sort_by,
            pagination=StudyPagination(page_nb=page_nb, page_size=page_size),
        )

        return matching_studies

    @bp.get(
        "/studies/{uuid}/comments",
        tags=[APITag.study_management],
        summary="Get comments",
    )
    def get_comments(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Get comments of study {uuid}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        study_id = sanitize_uuid(uuid)
        return study_service.get_comments(study_id, params)

    @bp.put(
        "/studies/{uuid}/comments",
        status_code=HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update comments",
        response_model=None,
    )
    def edit_comments(
        uuid: str,
        data: CommentsDto,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(
            f"Editing comments for study {uuid}",
            extra={"user": current_user.id},
        )
        new = data
        if not new:
            raise HTTPException(status_code=400, detail="empty body not authorized")
        study_id = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        study_service.edit_comments(study_id, new, params)

    @bp.post(
        "/studies/_import",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Import Study",
        response_model=str,
    )
    def import_study(
        study: bytes = File(...),
        groups: str = "",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        """
        Upload and import a compressed study from your computer to the Antares Web server.

        Args:
        - `study`: The binary content of the study file in ZIP or 7z format.
        - `groups`: The groups your study will belong to (Default: current user's groups).

        Returns:
        - The ID of the imported study.

        Raises:
        - 415 error if the archive is corrupted or in an unknown format.
        """
        logger.info("Importing new study", extra={"user": current_user.id})
        zip_binary = io.BytesIO(study)

        params = RequestParameters(user=current_user)
        group_ids = _split_comma_separated_values(groups, default=[group.id for group in current_user.groups])
        group_ids = [sanitize_uuid(gid) for gid in group_ids]

        try:
            uuid = study_service.import_study(zip_binary, group_ids, params)
        except BadArchiveContent as e:
            raise BadZipBinary(str(e))

        return uuid

    @bp.put(
        "/studies/{uuid}/upgrade",
        status_code=HTTPStatus.OK,
        tags=[APITag.study_management],
        summary="Upgrade study to the target version (or next version if not specified)",
    )
    def upgrade_study(
        uuid: str,
        target_version: str = "",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        """
        Upgrade a study to the target version or the next version if the target
        version is not specified.

        This method starts an upgrade task in the task manager.

        Args:
        - `uuid`: UUID of the study to upgrade.
        - `target_version`: target study version, or "" to upgrade to the next version.

        Returns:
        - The unique identifier of the task upgrading the study.
        """
        msg = (
            f"Upgrade study {uuid} to the version {target_version}"
            if target_version
            else f"Upgrade study {uuid} to the next version"
        )
        logger.info(msg, extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        # returns the task ID
        return study_service.upgrade_study(uuid, target_version, params)

    @bp.post(
        "/studies/{uuid}/copy",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Copy Study",
        response_model=str,
    )
    def copy_study(
        uuid: str,
        dest: str,
        with_outputs: bool = False,
        groups: str = "",
        use_task: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        """
        This endpoint enables you to duplicate a study and place it in a specified location.
        You can, for instance, copy a non-managed study to a managed workspace.

        Args:
        - `uuid`: The identifier of the study you wish to duplicate.
        - `dest`: The destination workspace where the study will be copied.
        - `with_outputs`: Indicates whether the study's outputs should also be duplicated.
        - `groups`: Specifies the groups to which your duplicated study will be assigned.
        - `use_task`: Determines whether this duplication operation should trigger a task.
          It is recommended and set as the default value: True.

        Returns:
        - The unique identifier of the task copying the study.
        """
        logger.info(
            f"Copying study {uuid} into new study '{dest}'",
            extra={"user": current_user.id},
        )
        source_uuid = uuid
        group_ids = _split_comma_separated_values(groups, default=[group.id for group in current_user.groups])
        group_ids = [sanitize_uuid(gid) for gid in group_ids]
        source_uuid_sanitized = sanitize_uuid(source_uuid)
        destination_name_sanitized = escape(dest)

        params = RequestParameters(user=current_user)

        task_id = study_service.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
            group_ids=group_ids,
            with_outputs=with_outputs,
            use_task=use_task,
            params=params,
        )

        return task_id

    @bp.put(
        "/studies/{uuid}/move",
        tags=[APITag.study_management],
        summary="Move study",
    )
    def move_study(
        uuid: str,
        folder_dest: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(
            f"Moving study {uuid} into folder '{folder_dest}'",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.move_study(uuid, folder_dest, params)

    @bp.post(
        "/studies",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Create a new empty study",
        response_model=str,
    )
    def create_study(
        name: str,
        version: str = "",
        groups: str = "",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Creating new study '{name}'", extra={"user": current_user.id})
        name_sanitized = escape(name)
        group_ids = _split_comma_separated_values(groups)
        group_ids = [sanitize_uuid(gid) for gid in group_ids]

        params = RequestParameters(user=current_user)
        uuid = study_service.create_study(name_sanitized, version, group_ids, params)

        return uuid

    @bp.get(
        "/studies/{uuid}/synthesis",
        tags=[APITag.study_management],
        summary="Return study synthesis",
        response_model=FileStudyTreeConfigDTO,
    )
    def get_study_synthesis(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(uuid)
        logger.info(
            f"Return a synthesis for study '{study_id}'",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_study_synthesis(study_id, params)

    @bp.get(
        "/studies/{uuid}/matrixindex",
        tags=[APITag.study_management],
        summary="Return study input matrix start date index",
        response_model=MatrixIndex,
    )
    def get_study_matrix_index(
        uuid: str,
        path: str = "",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(uuid)
        logger.info(
            f"Return the start date for input matrix '{study_id}'",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_input_matrix_startdate(study_id, path, params)

    @bp.get(
        "/studies/{uuid}/export",
        tags=[APITag.study_management],
        summary="Export Study",
        response_model=FileDownloadTaskDTO,
    )
    def export_study(
        uuid: str,
        no_output: t.Optional[bool] = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Exporting study {uuid}", extra={"user": current_user.id})
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=current_user)
        return study_service.export_study(uuid_sanitized, params, not no_output)

    @bp.delete(
        "/studies/{uuid}",
        status_code=HTTPStatus.OK,
        tags=[APITag.study_management],
        summary="Delete Study",
    )
    def delete_study(
        uuid: str,
        children: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Deleting study {uuid}", extra={"user": current_user.id})
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=current_user)
        study_service.delete_study(uuid_sanitized, children, params)

        return ""

    @bp.post(
        "/studies/{uuid}/output",
        status_code=HTTPStatus.ACCEPTED,
        tags=[APITag.study_outputs],
        summary="Import Output",
        response_model=str,
    )
    def import_output(
        uuid: str,
        output: bytes = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(
            f"Importing output for study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)

        zip_binary = io.BytesIO(output)

        params = RequestParameters(user=current_user)
        output_id = study_service.import_output(uuid_sanitized, zip_binary, params)
        return output_id

    @bp.put(
        "/studies/{uuid}/owner/{user_id}",
        tags=[APITag.study_permissions],
        summary="Change study owner",
    )
    def change_owner(
        uuid: str,
        user_id: int,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(
            f"Changing owner to {user_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        study_service.change_owner(uuid_sanitized, user_id, params)

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
    ) -> t.Any:
        logger.info(
            f"Adding group {group_id} to study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_uuid(group_id)
        params = RequestParameters(user=current_user)
        study_service.add_group(uuid_sanitized, group_id, params)

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
    ) -> t.Any:
        logger.info(
            f"Removing group {group_id} to study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_uuid(group_id)

        params = RequestParameters(user=current_user)
        study_service.remove_group(uuid_sanitized, group_id, params)

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
    ) -> t.Any:
        logger.info(
            f"Setting public mode to {mode} for study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        study_service.set_public_mode(uuid_sanitized, mode, params)

        return ""

    @bp.get(
        "/studies/_versions",
        tags=[APITag.study_management],
        summary="Show available study versions",
        response_model=t.List[str],
    )
    def get_study_versions(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        params = RequestParameters(user=current_user)
        logger.info("Fetching version list")
        return StudyService.get_studies_versions(params=params)

    @bp.get(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Get Study information",
        response_model=StudyMetadataDTO,
    )
    def get_study_metadata(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Fetching study {uuid} metadata", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        study_metadata = study_service.get_study_information(uuid, params)
        return study_metadata

    @bp.put(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Update Study information",
        response_model=StudyMetadataDTO,
    )
    def update_study_metadata(
        uuid: str,
        study_metadata_patch: StudyMetadataPatchDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(
            f"Updating metadata for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_metadata = study_service.update_study_information(uuid, study_metadata_patch, params)
        return study_metadata

    @bp.get(
        "/studies/{study_id}/outputs/{output_id}/variables",
        tags=[APITag.study_outputs],
        summary="Get outputs data variables",
    )
    def output_variables_information(
        study_id: str,
        output_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        logger.info(f"Fetching whole output of the simulation {output_id} for study {study_id}")
        params = RequestParameters(user=current_user)
        return study_service.output_variables_information(
            study_uuid=study_id,
            output_uuid=output_id,
            params=params,
        )

    @bp.get(
        "/studies/{study_id}/outputs/{output_id}/export",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def output_export(
        study_id: str,
        output_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        logger.info(f"Fetching whole output of the simulation {output_id} for study {study_id}")
        params = RequestParameters(user=current_user)
        return study_service.export_output(
            study_uuid=study_id,
            output_uuid=output_id,
            params=params,
        )

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def output_download(
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        request: Request,
        use_task: bool = False,
        tmp_export_file: Path = Depends(ftm.request_tmp_file),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        logger.info(
            f"Fetching batch outputs of simulation {output_id} for study {study_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        accept = request.headers.get("Accept")
        filetype = ExportFormat.from_dto(accept)

        content = study_service.download_outputs(
            study_id,
            output_id,
            data,
            use_task,
            filetype,
            params,
            tmp_export_file,
        )
        return content

    @bp.delete(
        "/studies/{study_id}/outputs/{output_id}",
        tags=[APITag.study_outputs],
        summary="Delete a simulation output",
    )
    def delete_output(
        study_id: str,
        output_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        logger.info(
            f"FDeleting output {output_id} from study {study_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.delete_output(
            study_id,
            output_id,
            params,
        )

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/_archive",
        tags=[APITag.study_outputs],
        summary="Archive output",
    )
    def archive_output(
        study_id: str,
        output_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        logger.info(
            f"Archiving of the output {output_id} of the study {study_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)

        content = study_service.archive_output(
            study_id,
            output_id,
            params,
        )
        return content

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/_unarchive",
        tags=[APITag.study_outputs],
        summary="Unarchive output",
    )
    def unarchive_output(
        study_id: str,
        output_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        logger.info(
            f"Unarchiving of the output {output_id} of the study {study_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)

        content = study_service.unarchive_output(
            study_id,
            output_id,
            False,
            params,
        )
        return content

    @bp.get(
        "/studies/{study_id}/outputs",
        summary="Get global information about a study simulation result",
        tags=[APITag.study_outputs],
        response_model=t.List[StudySimResultDTO],
    )
    def sim_result(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(
            f"Fetching output list for study {study_id}",
            extra={"user": current_user.id},
        )
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        content = study_service.get_study_sim_result(study_id, params)
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
    ) -> t.Any:
        logger.info(
            f"Setting output {output_id} as reference simulation for study {study_id}",
            extra={"user": current_user.id},
        )
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        params = RequestParameters(user=current_user)
        study_service.set_sim_reference(study_id, output_id, status, params)
        return ""

    @bp.put(
        "/studies/{study_id}/archive",
        summary="Archive a study",
        tags=[APITag.study_management],
    )
    def archive_study(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Archiving study {study_id}", extra={"user": current_user.id})
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        return study_service.archive(study_id, params)

    @bp.put(
        "/studies/{study_id}/unarchive",
        summary="Unarchive a study",
        tags=[APITag.study_management],
    )
    def unarchive_study(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        logger.info(f"Unarchiving study {study_id}", extra={"user": current_user.id})
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        return study_service.unarchive(study_id, params)

    @bp.get(
        "/studies/{uuid}/disk-usage",
        summary="Compute study disk usage",
        tags=[APITag.study_management],
    )
    def study_disk_usage(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> int:
        """
        Compute disk usage of an input study

        Args:
        - `uuid`: the UUID of the study whose disk usage is to be retrieved.

        Return:
        - The disk usage of the study in bytes.
        """
        logger.info("Retrieving study disk usage", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return study_service.get_disk_usage(uuid=uuid, params=params)

    return bp
