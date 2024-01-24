import http
import io
import json
import logging
import pathlib
import typing as t
from enum import Enum

import pandas as pd
from fastapi import APIRouter, Body, Depends, File, HTTPException
from fastapi.params import Param, Query
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from antarest.core.config import Config
from antarest.core.exceptions import IncorrectPathError
from antarest.core.jwt import JWTUser
from antarest.core.model import SUB_JSON
from antarest.core.requests import RequestParameters
from antarest.core.swagger import get_path_examples
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)

# noinspection SpellCheckingInspection

CONTENT_TYPES = {
    # (Portable Document Format)
    ".pdf": ("application/pdf", None),
    # (Microsoft Excel)
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", None),
    # (Microsoft Word)
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", None),
    # (Microsoft PowerPoint)
    ".pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", None),
    # (LibreOffice Writer)
    ".odt": ("application/vnd.oasis.opendocument.text", None),
    # (LibreOffice Calc)
    ".ods": ("application/vnd.oasis.opendocument.spreadsheet", None),
    # (LibreOffice Impress)
    ".odp": ("application/vnd.oasis.opendocument.presentation", None),
    # (Comma-Separated Values)
    ".csv": ("text/csv", "utf-8"),
    # (Tab-Separated Values)
    ".tsv": ("text/tab-separated-values", "utf-8"),
    # (Plain Text)
    ".txt": ("text/plain", "utf-8"),
    # (JSON)
    ".json": ("application/json", "utf-8"),
}


class ExpectedFormatTypes(Enum):
    XLSX = "xlsx"
    CSV = "csv"


def create_raw_study_routes(
    study_service: StudyService,
    config: Config,
) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies/{uuid}/raw",
        tags=[APITag.study_raw_data],
        summary="Retrieve Raw Data from Study: JSON, Text, or File Attachment",
    )
    def get_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        depth: int = 3,
        formatted: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.Any:
        """
        Fetches raw data from a study, and returns the data
        in different formats based on the file type, or as a JSON response.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to fetch.
        - `depth`: The depth of the data to retrieve.
        - `formatted`: A flag specifying whether the data should be returned in a formatted manner.

        Returns the fetched data: a JSON object (in most cases), a plain text file
        or a file attachment (Microsoft Office document, CSV/TSV file...).
        """
        logger.info(
            f"📘 Fetching data at {path} (depth={depth}) from study {uuid}",
            extra={"user": current_user.id},
        )
        parameters = RequestParameters(user=current_user)
        output = study_service.get(uuid, path, depth=depth, formatted=formatted, params=parameters)

        if isinstance(output, bytes):
            # Guess the suffix form the target data
            resource_path = pathlib.PurePosixPath(path)
            parent_cfg = study_service.get(uuid, str(resource_path.parent), depth=2, formatted=True, params=parameters)
            child = parent_cfg[resource_path.name]
            suffix = pathlib.PurePosixPath(child).suffix

            content_type, encoding = CONTENT_TYPES.get(suffix, (None, None))
            if content_type == "application/json":
                # Use `JSONResponse` to ensure to return a valid JSON response
                # that checks `NaN` and `Infinity` values.
                try:
                    output = json.loads(output)
                    return JSONResponse(content=output)
                except ValueError as exc:
                    raise HTTPException(
                        status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
                        detail=f"Invalid JSON configuration in path '{path}': {exc}",
                    ) from None
            elif encoding:
                try:
                    response = PlainTextResponse(output, media_type=content_type)
                    response.charset = encoding
                    return response

                except ValueError as exc:
                    raise HTTPException(
                        status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
                        detail=f"Invalid plain text configuration in path '{path}': {exc}",
                    ) from None
            elif content_type:
                headers = {"Content-Disposition": f"attachment; filename={resource_path.name}"}
                return StreamingResponse(
                    io.BytesIO(output),
                    media_type=content_type,
                    headers=headers,
                )
            else:
                # Unknown content types are considered binary,
                # because it's better to avoid raising an exception.
                return Response(content=output, media_type="application/octet-stream")

        # We want to allow `NaN`, `+Infinity`, and `-Infinity` values in the JSON response
        # even though they are not standard JSON values because they are supported in JavaScript.
        # Additionally, we cannot use `orjson` because, despite its superior performance, it converts
        # `NaN` and other values to `null`, even when using a custom encoder.
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
        status_code=http.HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update data by posting formatted data",
    )
    def edit_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        data: SUB_JSON = Body(default=""),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Updates raw data for a study by posting formatted data.

        > NOTE: use the PUT endpoint to upload a file.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `data`: The formatted data to be posted. Defaults to an empty string.
          The data could be a JSON object, or a simple string.
        """
        logger.info(
            f"Editing data at {path} for study {uuid}",
            extra={"user": current_user.id},
        )
        path = sanitize_uuid(path)
        params = RequestParameters(user=current_user)
        study_service.edit_study(uuid, path, data, params)

    @bp.put(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update data by posting a Raw file",
    )
    def replace_study_file(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        file: bytes = File(...),
        create_missing: bool = Query(
            False,
            description="Create file or parent directories if missing.",
        ),  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Update raw data for a study by posting a raw file.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `file`: The raw file to be posted (e.g. a CSV file opened in binary mode).
        - `create_missing`: Flag to indicate whether to create file or parent directories if missing.
        """
        logger.info(
            f"Uploading new data file at {path} for study {uuid}",
            extra={"user": current_user.id},
        )
        path = sanitize_uuid(path)
        params = RequestParameters(user=current_user)
        study_service.edit_study(uuid, path, file, params, create_missing=create_missing)

    @bp.get(
        "/studies/{uuid}/raw/download",
        summary="Download a matrix in a given format",
        tags=[APITag.study_raw_data],
        response_class=StreamingResponse,
    )
    def get_matrix(
        uuid: str,
        path: str,
        format: ExpectedFormatTypes,
        header: bool = True,
        index: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> StreamingResponse:
        # todo: Question Alexander, est-ce qu'on veut toujours pouvoir importer en format raw (.txt) ?
        parameters = RequestParameters(user=current_user)
        json_matrix = study_service.get(uuid, path, depth=3, formatted=True, params=parameters)
        expected_keys = ["data", "index", "columns"]
        for key in expected_keys:
            if key not in json_matrix:
                raise IncorrectPathError(f"The path filled does not correspond to a matrix : {path}")
        df_matrix = pd.DataFrame(data=json_matrix["data"], columns=json_matrix["columns"], index=json_matrix["index"])
        if index:
            # todo: Ne marche que pour les matrices classiques pas les autres ...
            matrix_index = study_service.get_input_matrix_startdate(uuid, path, parameters)
            time_column = pd.date_range(
                start=matrix_index.start_date, periods=len(df_matrix), freq=matrix_index.level.value[0]
            )
            df_matrix.insert(0, "Time", time_column)

        export_file_download = study_service.file_transfer_manager.request_download(
            f"{pathlib.Path(path).stem}.{format.value}",
            f"Exporting matrix {pathlib.Path(path).stem} to format {format.value} for study {uuid}",
            current_user,
            create_task=False,
        )
        export_path = pathlib.Path(export_file_download.path)
        export_id = export_file_download.id

        try:
            _create_matrix_files(df_matrix, header, index, format, export_path)
            study_service.file_transfer_manager.set_ready(export_id, create_task=False)
        except Exception as e:
            study_service.file_transfer_manager.fail(export_id, str(e))
            raise e
            # todo: Maybe this should be wrapped by an HTTP Exception

        def iter_file() -> t.Iterator[bytes]:
            with export_path.open(mode="rb") as file:
                yield from file

        # todo: tester la perf du StreamingResponse VS FileResponse

        return StreamingResponse(
            iter_file(),
            headers={"Content-Disposition": f'attachment; filename="{export_file_download.filename}"'},
            media_type="application/octet-stream",
        )

    @bp.get(
        "/studies/{uuid}/raw/validate",
        summary="Launch test validation on study",
        tags=[APITag.study_raw_data],
        response_model=t.List[str],
    )
    def validate(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.List[str]:
        """
        Launches test validation on the raw data of a study.
        The validation is done recursively on all the files in the study

        Parameters:
        - `uuid`: The UUID of the study.

        Response:
        - A list of strings indicating validation errors (if any) for the study's raw data.
          The list is empty if no errors were found.
        """
        logger.info(
            f"Validating data for study {uuid}",
            extra={"user": current_user.id},
        )
        return study_service.check_errors(uuid)

    return bp


def _create_matrix_files(
    df_matrix: pd.DataFrame, header: bool, index: bool, format: ExpectedFormatTypes, export_path: pathlib.Path
) -> None:
    if format == ExpectedFormatTypes.CSV:
        # todo: Question Alexander : sep = , ou ; pour les csv. Idem pour les xlsx
        # Perso je préfère le ; mais si on veut réimporter c'est ptetr chiant
        df_matrix.to_csv(
            export_path,
            sep="\t",
            header=header,
            index=index,
            float_format="%.6f",
        )
    else:
        df_matrix.to_excel(
            export_path,
            header=header,
            index=index,
            float_format="%.6f",
        )
