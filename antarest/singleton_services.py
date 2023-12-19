import time
from pathlib import Path
from typing import Dict, List, cast

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.core.utils.utils import get_local_path
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.utils import (
    SESSION_ARGS,
    Module,
    create_archive_worker,
    create_core_services,
    create_matrix_gc,
    create_simulator_worker,
    create_watcher,
    init_db_engine,
)

SLEEP_TIME = 2


def _init(config_file: Path, services_list: List[Module]) -> Dict[Module, IService]:
    res = get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)
    engine = init_db_engine(
        config_file,
        config,
        False,
    )
    DBSessionMiddleware(None, custom_engine=engine, session_args=cast(Dict[str, bool], SESSION_ARGS))
    configure_logger(config)

    (
        cache,
        event_bus,
        task_service,
        ft_manager,
        login_service,
        matrix_service,
        study_service,
    ) = create_core_services(None, config)

    services: Dict[Module, IService] = {}

    if Module.WATCHER in services_list:
        watcher = create_watcher(config=config, application=None, study_service=study_service)
        services[Module.WATCHER] = watcher

    if Module.MATRIX_GC in services_list:
        matrix_gc = create_matrix_gc(
            config=config,
            application=None,
            study_service=study_service,
            matrix_service=matrix_service,
        )
        services[Module.MATRIX_GC] = matrix_gc

    if Module.ARCHIVE_WORKER in services_list:
        worker = create_archive_worker(config, "test", event_bus=event_bus)
        services[Module.ARCHIVE_WORKER] = worker

    if Module.SIMULATOR_WORKER in services_list:
        worker = create_simulator_worker(config, matrix_service=matrix_service, event_bus=event_bus)
        services[Module.SIMULATOR_WORKER] = worker

    if Module.AUTO_ARCHIVER in services_list:
        auto_archive_service = AutoArchiveService(study_service, config)
        services[Module.AUTO_ARCHIVER] = auto_archive_service

    return services


def start_all_services(config_file: Path, services_list: List[Module]) -> None:
    services = _init(config_file, services_list)
    for service in services:
        services[service].start(threaded=True)
    # this loop may be interrupted using Crl+C
    while True:
        time.sleep(SLEEP_TIME)
