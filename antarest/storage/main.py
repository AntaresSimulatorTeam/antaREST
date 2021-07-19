from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.storage.business.rawstudy.exporter_service import ExporterService
from antarest.storage.business.rawstudy.importer_service import ImporterService
from antarest.storage.business.rawstudy.patch_service import PatchService
from antarest.storage.business.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.storage.business.common.uri_resolver_service import (
    UriResolverService,
)
from antarest.storage.business.rawstudy.watcher import Watcher
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.repository.study_metadata import StudyMetadataRepository
from antarest.storage.service import StudyService
from antarest.storage.web.areas_blueprint import create_study_area_routes
from antarest.storage.web.studies_blueprint import create_study_routes


def build_storage(
    application: FastAPI,
    config: Config,
    user_service: LoginService,
    matrix_service: MatrixService,
    metadata_repository: Optional[StudyMetadataRepository] = None,
    storage_service: Optional[StudyService] = None,
    patch_service: Optional[PatchService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> StudyService:
    """
    Storage module linking dependencies.

    Args:
        application: flask application
        config: server config
        user_service: user service facade
        matrix_service: matrix store service
        metadata_repository: used by testing to inject mock. Let None to use true instantiation
        storage_service: used by testing to inject mock. Let None to use true instantiation
        patch_service: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns:

    """

    path_resources = config.resources_path

    resolver = UriResolverService(config, matrix_service=matrix_service)
    study_factory = StudyFactory(matrix=matrix_service, resolver=resolver)
    metadata_repository = metadata_repository or StudyMetadataRepository()

    patch_service = patch_service or PatchService()

    study_service = RawStudyService(
        config=config,
        study_factory=study_factory,
        path_resources=path_resources,
        patch_service=patch_service,
    )
    importer_service = ImporterService(
        study_service=study_service,
        study_factory=study_factory,
    )
    exporter_service = ExporterService(
        study_service=study_service,
        study_factory=study_factory,
        config=config,
    )

    storage_service = storage_service or StudyService(
        study_service=study_service,
        importer_service=importer_service,
        exporter_service=exporter_service,
        user_service=user_service,
        repository=metadata_repository,
        event_bus=event_bus,
    )

    watcher = Watcher(config=config, service=storage_service)
    watcher.start()

    application.include_router(create_study_routes(storage_service, config))
    application.include_router(
        create_study_area_routes(storage_service, config)
    )

    return storage_service
