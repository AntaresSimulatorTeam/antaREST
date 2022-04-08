import json
import logging
import shutil
from pathlib import Path
from typing import Optional, Any, cast, List, Dict

import yaml
from filelock import FileLock

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigData
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService

logger = logging.getLogger(__name__)


class AdequacyPatchExtension(ILauncherExtension):
    EXTENSION_NAME = "adequacy_patch"

    def __init__(self, study_service: StudyService, config: Config):
        self.study_service = study_service
        self.tmp_dir = (
            config.storage.tmp_dir
            / f"ext_{AdequacyPatchExtension.EXTENSION_NAME}"
        )
        self.config_data_repo = ConfigDataRepository()
        self.tmp_dir.mkdir(exist_ok=True)

    def get_name(self) -> str:
        return AdequacyPatchExtension.EXTENSION_NAME

    def after_export_flat_hook(
        self,
        job_id: str,
        study_id: str,
        study_export_path: Path,
        launcher_opts: Any,
    ) -> None:
        logger.info("Applying adequacy patch postprocessing script")
        if "legacy" in launcher_opts and launcher_opts["legacy"]:
            logger.info("Using legacy quadratic mode")
            post_processing_file = (
                Path(__file__).parent
                / "resources"
                / "post-processing-legacy.R"
            )
        else:
            logger.info("Using linearized mode")
            post_processing_file = (
                Path(__file__).parent / "resources" / "post-processing.R"
            )
        shutil.copy(
            post_processing_file, study_export_path / "post-processing.R"
        )

        study = self.study_service.storage_service.raw_study_service.study_factory.create_from_fs(
            study_export_path, study_id, use_cache=False
        )
        user_config = study.tree.get(["user"])
        assert_this("flowbased" in user_config)
        adequacy_patch_config = yaml.safe_load(
            cast(
                bytes, study.tree.get(["user", "adequacypatch", "config.yml"])
            )
        )
        assert_this("areas" in adequacy_patch_config)
        self.prepare_study_for_adq_patch(job_id, study, adequacy_patch_config)

    def prepare_study_for_adq_patch(
        self, job_id: str, study: FileStudy, adq_patch_config: JSON
    ) -> Dict[str, bool]:
        area_to_turn_on: List[str] = [
            transform_name_to_id(area_id)
            for area_id in adq_patch_config.get("areas", [])
        ]
        original_area_status: Dict[str, bool] = {}
        for area_id, area in study.config.areas.items():
            # area.filters_synthesis
            original_area_status[area_id] = "hourly" in area.filters_year
            if (
                not original_area_status[area_id]
                and area_id in area_to_turn_on
            ):
                study.tree.save(
                    ", ".join([*area.filters_year, "hourly"]),
                    [
                        "input",
                        "areas",
                        area_id,
                        "optimization",
                        "filter-year-by-year",
                    ],
                )

        with FileLock(self.tmp_dir / "data.lock"):
            with db():
                key = "ADEQUACY_PATCH_DATA"
                data = self.config_data_repo.get_json(key) or {}
                data[job_id] = original_area_status
                with open(
                    study.config.study_path
                    / "user"
                    / "adequacypatch"
                    / "hourly-areas.yml",
                    "w",
                ) as fh:
                    yaml.dump(original_area_status, fh)
                self.config_data_repo.save(
                    ConfigData(owner=0, key=key, value=json.dumps(data))
                )
        return original_area_status

    def before_import_hook(
        self,
        job_id: str,
        study_id: str,
        study_output_path: Path,
        ext_opts: Any,
    ) -> None:
        pass
