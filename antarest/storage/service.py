import logging
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, IO, Optional, cast

import werkzeug
from uuid import uuid4

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus, Event, EventType
from antarest.login.model import User, Role, Group
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.importer_service import ImporterService
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.business.raw_study_service import StudyService
from antarest.storage.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
)
from antarest.storage.repository.metadata import StudyMetadataRepository
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
)

logger = logging.getLogger(__name__)


class UserHasNotPermissionError(werkzeug.exceptions.Forbidden):
    pass


class StorageService:
    def __init__(
        self,
        study_service: StudyService,
        importer_service: ImporterService,
        exporter_service: ExporterService,
        repository: StudyMetadataRepository,
        event_bus: IEventBus,
    ):
        self.study_service = study_service
        self.importer_service = importer_service
        self.exporter_service = exporter_service
        self.repository = repository
        self.event_bus = event_bus

    def get(self, route: str, depth: int, params: RequestParameters) -> JSON:
        uuid, url = StorageServiceUtils.extract_info_from_url(route)
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)

        if isinstance(md, RawStudy):
            return self.study_service.get(md, url, depth)

        raise StudyTypeUnsupported(
            f"Study {uuid} with type {md.type} not recognized"
        )

    def _get_study_metadatas(self, params: RequestParameters) -> List[Study]:

        return list(
            filter(
                lambda md: self._assert_permission(
                    params.user, md, raising=False
                ),
                self.repository.get_all(),
            )
        )

    def get_studies_information(self, params: RequestParameters) -> JSON:
        return {
            md.id: self.study_service.get_study_information(md)
            for md in self._get_study_metadatas(params)
        }

    def get_study_information(
        self, uuid: str, params: RequestParameters
    ) -> JSON:
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        return self.study_service.get_study_information(md)

    def get_study_path(self, uuid: str, params: RequestParameters) -> Path:
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)

        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        return self.study_service.get_study_path(md)

    def create_study(self, study_name: str, params: RequestParameters) -> str:
        sid = str(uuid4())
        study_path = str(self.study_service.get_default_workspace_path() / sid)
        md = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=study_path,
        )
        md = self.study_service.create_study(md)
        self._save_metadata(md, params.user)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, md.to_json_summary())
        )
        return str(md.id)

    def sync_studies_on_disk(self, folders: List[StudyFolder]) -> None:

        # delete orphan studies on database
        paths = [str(f.path) for f in folders]
        for md in self.repository.get_all():
            if md.path not in paths:
                logger.info(
                    f"Study={md.id} is not present in disk and will be deleted"
                )
                self.event_bus.push(
                    Event(EventType.STUDY_DELETED, md.to_json_summary())
                )
                self.repository.delete(md.id)

        # Add new studies
        paths = [md.path for md in self.repository.get_all()]
        for folder in folders:
            if str(folder.path) not in paths:
                md = RawStudy(
                    id=str(uuid4()),
                    name=folder.path.name,
                    path=str(folder.path),
                    workspace=folder.workspace,
                    owner=User(id=0),
                    groups=folder.groups,
                )

                md.content_status = self._analyse_study(md)

                logger.info(f"Study={md.id} appears on disk and will be added")
                self.event_bus.push(
                    Event(EventType.STUDY_CREATED, md.to_json_summary())
                )
                self.repository.save(md)

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        params: RequestParameters,
    ) -> str:
        src_md = self._get_metadata(src_uuid)
        self._assert_permission(params.user, src_md)

        if not isinstance(src_md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {src_uuid} with type {src_md.type} not recognized"
            )

        dest_md = deepcopy(src_md)
        dest_md.id = str(uuid4())
        dest_md.name = dest_study_name
        dest_md.workspace = DEFAULT_WORKSPACE_NAME
        dest_md.path = str(
            self.study_service.get_default_workspace_path() / dest_md.id
        )

        md = self.study_service.copy_study(src_md, dest_md)
        self._save_metadata(md, params.user)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, md.to_json_summary())
        )
        return str(md.id)

    def export_study(
        self,
        uuid: str,
        params: RequestParameters,
        compact: bool = False,
        outputs: bool = True,
    ) -> BytesIO:
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        return self.exporter_service.export_study(md, compact, outputs)

    def delete_study(self, uuid: str, params: RequestParameters) -> None:
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        self.study_service.delete_study(md)
        self.repository.delete(md.id)
        self.event_bus.push(
            Event(EventType.STUDY_DELETED, md.to_json_summary())
        )

    def delete_output(
        self, uuid: str, output_name: str, params: RequestParameters
    ) -> None:
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        self.study_service.delete_output(md, output_name)
        self.event_bus.push(
            Event(EventType.STUDY_EDITED, md.to_json_summary())
        )

    def get_matrix(self, route: str, params: RequestParameters) -> bytes:
        uuid, path = StorageServiceUtils.extract_info_from_url(route)
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        return self.exporter_service.get_matrix(md, path)

    def upload_matrix(
        self, path: str, data: bytes, params: RequestParameters
    ) -> None:
        uuid, _ = StorageServiceUtils.extract_info_from_url(path)
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        self.importer_service.upload_matrix(md, path, data)

        self.event_bus.push(
            Event(EventType.STUDY_EDITED, md.to_json_summary())
        )

    def import_study(
        self, stream: IO[bytes], params: RequestParameters
    ) -> str:
        sid = str(uuid4())
        path = str(self.study_service.get_default_workspace_path() / sid)
        md = RawStudy(id=sid, workspace=DEFAULT_WORKSPACE_NAME, path=path)
        md = self.importer_service.import_study(md, stream)
        status = self._analyse_study(md)
        self._save_metadata(md, owner=params.user, content_status=status)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, md.to_json_summary())
        )
        return str(md.id)

    def import_output(
        self, uuid: str, stream: IO[bytes], params: RequestParameters
    ) -> JSON:
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        res = self.importer_service.import_output(md, stream)
        return res

    def edit_study(
        self, route: str, new: JSON, params: RequestParameters
    ) -> JSON:
        uuid, url = StorageServiceUtils.extract_info_from_url(route)
        md = self._get_metadata(uuid)
        self._assert_permission(params.user, md)
        if not isinstance(md, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {md.type} not recognized"
            )

        updated = self.study_service.edit_study(md, url, new)
        self.event_bus.push(
            Event(EventType.STUDY_EDITED, md.to_json_summary())
        )
        return updated

    def _save_metadata(
        self,
        metadata: RawStudy,
        owner: Optional[User] = None,
        content_status: StudyContentStatus = StudyContentStatus.VALID,
        group: Optional[Group] = None,
    ) -> None:
        if not owner and not group:
            raise UserHasNotPermissionError

        info = self.study_service.get_study_information(metadata)["antares"]

        metadata.name = info["caption"]
        metadata.version = info["version"]
        metadata.author = info["author"]
        metadata.created_at = datetime.fromtimestamp(info["created"])
        metadata.updated_at = datetime.fromtimestamp(info["lastsave"])
        metadata.content_status = content_status

        if owner:
            metadata.owner = owner
        if group:
            metadata.groups = [group]
        self.repository.save(metadata)

    def _get_metadata(self, uuid: str) -> Study:

        md = self.repository.get(uuid)
        if not md:
            sanitized = StorageServiceUtils.sanitize(uuid)
            logger.warning(
                f"Study %s not found in metadata db",
                sanitized,
            )
            raise StudyNotFoundError(uuid)
        return md

    def _assert_permission(
        self,
        user: Optional[User],
        md: Optional[Study],
        raising: bool = True,
    ) -> bool:
        if not user:
            raise UserHasNotPermissionError()

        if not md:
            raise ValueError("Metadata is None")

        if user.role == Role.ADMIN:
            return True

        is_owner = user == md.owner
        inside_group = (
            md.groups
            and user.groups
            and any(g in md.groups for g in user.groups)
        )

        if not is_owner and not inside_group:
            if raising:
                raise UserHasNotPermissionError()
            else:
                return False

        return True

    def _analyse_study(self, metadata: RawStudy) -> StudyContentStatus:
        try:
            if self.study_service.check_errors(metadata):
                return StudyContentStatus.WARNING
            else:
                return StudyContentStatus.VALID
        except Exception as e:
            logger.error(e)
            return StudyContentStatus.ERROR
