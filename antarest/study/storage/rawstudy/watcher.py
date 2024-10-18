# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import re
import tempfile
from html import escape
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from time import sleep, time
from typing import List, Optional

from antares.study.version.upgrade_app import is_temporary_upgrade_dir
from filelock import FileLock

from antarest.core.config import Config
from antarest.core.exceptions import CannotScanInternalWorkspace
from antarest.core.interfaces.service import IService
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskResult, TaskType
from antarest.core.tasks.service import ITaskService, TaskUpdateNotifier
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.login.model import Group
from antarest.study.model import DEFAULT_WORKSPACE_NAME, StudyFolder
from antarest.study.service import StudyService
from antarest.study.storage.utils import get_folder_from_workspace, get_workspace_from_config
from antarest.study.storage.variantstudy.model.command.generate_thermal_cluster_timeseries import is_ts_gen_tmp_dir

logger = logging.getLogger(__name__)


class _LogScanDuration:
    """Functional object use to log the scanning duration of a workspace."""

    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name

    def __call__(self, duration: float) -> None:
        logger.info(f"Workspace {self.workspace_name} scanned in {duration}s")


class Watcher(IService):
    """
    Files Watcher to listen raw studies changes and trigger a database update.
    """

    LOCK = Path(tempfile.gettempdir()) / "watcher"
    SCAN_LOCK = Path(tempfile.gettempdir()) / "scan.lock"

    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        task_service: ITaskService,
    ):
        super(Watcher, self).__init__()
        self.study_service = study_service
        self.task_service = task_service
        self.config = config
        self.should_stop = False
        self.allowed_to_start = not config.storage.watcher_lock or Watcher._get_lock(config.storage.watcher_lock_delay)

    def start(self, threaded: bool = True) -> None:
        self.should_stop = False
        if self.allowed_to_start:
            super(Watcher, self).start(threaded=threaded)

    def stop(self) -> None:
        self.should_stop = True

    @staticmethod
    def _get_lock(lock_delay: int) -> bool:
        """
        Force watcher to run only one by access a lock on filesystem.

        Returns: true if watcher get the lock, false else.

        """
        with FileLock(f"{Watcher.LOCK}.lock"):
            start = int(f"0{Watcher.LOCK.read_text()}") if Watcher.LOCK.exists() else 0
            now = int(time())
            if now - start > lock_delay:
                Watcher.LOCK.write_text(str(now))
                logger.info("Watcher get lock")
                return True
            else:
                logger.info("Watcher doesn't get lock")
                return False

    def _loop(self) -> None:
        try:
            logger.info(
                "Removing duplicates, this is a temporary fix that should be removed when previous duplicates are removed"
            )
            with db():
                # in this part full `Read` rights over studies are granted to this function
                self.study_service.remove_duplicates()
        except Exception as e:
            logger.error("Unexpected error when removing duplicates", exc_info=e)

        while True:
            try:
                if not self.should_stop:
                    self.scan()
            except Exception as e:
                logger.error("Unexpected error when scanning workspaces", exc_info=e)
            sleep(2)

    def _rec_scan(
        self,
        path: Path,
        workspace: str,
        groups: List[Group],
        filter_in: List[str],
        filter_out: List[str],
        max_depth: Optional[int] = None,
    ) -> List[StudyFolder]:
        try:
            if (path / "AW_NO_SCAN").exists():
                logger.info(f"No scan directive file found. Will skip further scan of folder {path}")
                return []

            if is_temporary_upgrade_dir(path):
                logger.info(f"Upgrade temporary folder found. Will skip further scan of folder {path}")
                return []

            if is_ts_gen_tmp_dir(path):
                logger.info(f"TS generation temporary folder found. Will skip further scan of folder {path}")
                return []

            if (path / "study.antares").exists():
                logger.debug(f"Study {path.name} found in {workspace}")
                return [StudyFolder(path, workspace, groups)]

            if max_depth is not None and max_depth <= 0:
                logger.info(f"Scan was configured to not go any deeper")
                return []

            else:
                folders: List[StudyFolder] = list()
                if path.is_dir():
                    for child in path.iterdir():
                        if max_depth is not None:
                            max_depth = max_depth - 1
                        try:
                            if (
                                (child.is_dir())
                                and any([re.search(regex, child.name) for regex in filter_in])
                                and not any([re.search(regex, child.name) for regex in filter_out])
                            ):
                                folders = folders + self._rec_scan(
                                    child, workspace, groups, filter_in, filter_out, max_depth
                                )
                        except Exception as e:
                            logger.error(f"Failed to scan dir {child}", exc_info=e)
                return folders
        except Exception as e:
            logger.error(f"Failed to scan dir {path}", exc_info=e)
            return []

    def oneshot_scan(
        self,
        params: RequestParameters,
        recursive: bool,
        workspace: Optional[str] = None,
        path: Optional[str] = None,
    ) -> str:
        """
        Scan a folder and add studies found to database.

        Args:
            params: user parameters
            workspace: workspace to scan
            path: relative path to folder to scan
        """

        # noinspection PyUnusedLocal
        def scan_task(notifier: TaskUpdateNotifier) -> TaskResult:
            self.scan(recursive, workspace, path)
            return TaskResult(success=True, message="Scan completed")

        return self.task_service.add_task(
            action=scan_task,
            name=f"Scanning {workspace}/{path}",
            task_type=TaskType.SCAN,
            ref_id=None,
            progress=None,
            custom_event_messages=None,
            request_params=params,
        )

    def scan(
        self,
        recursive: bool = True,
        workspace_name: Optional[str] = None,
        workspace_directory_path: Optional[str] = None,
    ) -> None:
        """
        Scan recursively list of studies present on disk. Send updated list to study service.
        Returns:

        """
        stopwatch = StopWatch()
        studies: List[StudyFolder] = list()
        directory_path: Optional[Path] = None

        # max depth when we call _rec_scan
        max_depth = None if recursive else 1

        if workspace_directory_path is not None and workspace_name:
            if workspace_name == DEFAULT_WORKSPACE_NAME:
                raise CannotScanInternalWorkspace

            workspace = get_workspace_from_config(self.config, workspace_name)
            directory_path = get_folder_from_workspace(workspace, workspace_directory_path)

            groups = [Group(id=escape(g), name=escape(g)) for g in workspace.groups]
            studies = self._rec_scan(
                directory_path, workspace_name, groups, workspace.filter_in, workspace.filter_out, max_depth=max_depth
            )
        elif workspace_directory_path is None and workspace_name is None:
            for name, workspace in self.config.storage.workspaces.items():
                if name != DEFAULT_WORKSPACE_NAME:
                    path = Path(workspace.path)
                    groups = [Group(id=escape(g), name=escape(g)) for g in workspace.groups]
                    studies = studies + self._rec_scan(
                        path, name, groups, workspace.filter_in, workspace.filter_out, max_depth=max_depth
                    )
                    stopwatch.log_elapsed(_LogScanDuration(name))
        else:
            raise ValueError("Both workspace_name and directory_path must be specified")
        with db():
            logger.info(f"Waiting for FileLock to synchronize {directory_path or 'all studies'}")
            with FileLock(Watcher.SCAN_LOCK):
                logger.info(f"FileLock acquired to synchronize for {directory_path or 'all studies'}")
                self.study_service.sync_studies_on_disk(studies, directory_path, recursive)
                stopwatch.log_elapsed(
                    lambda x: logger.info(f"{directory_path or 'All studies'} synchronized in {x}s"),
                    since_start=True,
                )
