import copy
import shutil
from pathlib import Path
from typing import List, Optional
from zipfile import ZipFile

from antarest.common.config import Config
from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.web.exceptions import StudyNotFoundError


class RawStudyService:
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        path_resources: Path,
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.path_resources: Path = path_resources

    def check_study_exists(self, metadata: RawStudy) -> None:
        """
        Check study on filesystem.

        Args:
            metadata: study

        Returns: none or raise error if not found

        """
        if not self.study_exists(metadata):
            raise StudyNotFoundError(
                f"Study with the uuid {metadata.id} does not exist."
            )

    def check_errors(self, metadata: RawStudy) -> List[str]:
        """
        Check study antares data integrity
        Args:
            metadata: study

        Returns: list of non integrity inside study

        """
        path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(path, metadata.id)
        return study.check_errors(study.get())

    def study_exists(self, metadata: RawStudy) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """
        return (self.get_study_path(metadata) / "study.antares").is_file()

    def get_study_uuids(self, workspace: Optional[str] = None) -> List[str]:
        """
        List study presents on disk
        Args:
            workspace: specify workspace

        Returns: list of study present in workspace

        """
        folders: List[Path] = []
        if workspace:
            folders = list(self.get_workspace_path(workspace).iterdir())
        else:
            for w in self.config.storage.workspaces:
                folders += list(self.get_workspace_path(w).iterdir())

        studies_list = [
            path.name for path in folders if (path / "study.antares").is_file()
        ]
        # sorting needed for test
        return sorted(studies_list)

    def get(self, metadata: RawStudy, url: str = "", depth: int = 3) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path

        Returns: study data formatted in json

        """
        self.check_study_exists(metadata)
        study_path = self.get_study_path(metadata)

        _, study = self.study_factory.create_from_fs(study_path, metadata.id)
        parts = [item for item in url.split("/") if item]

        data = study.get(parts, depth=depth)
        del study
        return data

    def get_study_information(self, metadata: RawStudy) -> JSON:
        """
        Get information present in study.antares file
        Args:
            metadata: study

        Returns: study.antares data formatted in json

        """
        config = StudyConfig(
            study_path=self.get_study_path(metadata), study_id=metadata.id
        )
        study = self.study_factory.create_from_config(config)
        return study.get(url=["study"])

    def get_workspace_path(self, workspace: str) -> Path:
        """
        Retrieve workspace path from config

        Args:
            workspace: workspace name

        Returns: path

        """
        return self.config.storage.workspaces[workspace].path

    def get_default_workspace_path(self) -> Path:
        """
        Get path of default workspace
        Returns: path

        """
        return self.get_workspace_path(DEFAULT_WORKSPACE_NAME)

    def get_study_path(self, metadata: RawStudy) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        path: Path = Path(metadata.path)
        return path

    def create_study(self, metadata: RawStudy) -> RawStudy:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """
        empty_study_zip = self.path_resources / "empty-study.zip"

        path_study = self.get_study_path(metadata)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.get(metadata, url="", depth=10)
        StorageServiceUtils.update_antares_info(metadata, study_data)

        _, study = self.study_factory.create_from_fs(path_study, metadata.id)
        study.save(study_data["study"], url=["study"])

        metadata.path = str(path_study)
        return metadata

    def copy_study(self, src_meta: RawStudy, dest_meta: RawStudy) -> RawStudy:
        """
        Copy study to a new destination
        Args:
            src_meta: source study
            dest_meta: destination study

        Returns: destination study

        """
        self.check_study_exists(src_meta)
        src_path = self.get_study_path(src_meta)

        config, study = self.study_factory.create_from_fs(
            src_path, src_meta.id
        )
        data_source = study.get()
        del study

        config.path = Path(dest_meta.path)
        data_destination = copy.deepcopy(data_source)

        StorageServiceUtils.update_antares_info(dest_meta, data_destination)
        if "output" in data_destination:
            del data_destination["output"]
        config.outputs = {}

        study = self.study_factory.create_from_config(config)
        study.save(data_destination)
        del study
        return dest_meta

    def delete_study(self, metadata: RawStudy) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        self.check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        shutil.rmtree(study_path)

    def delete_output(self, metadata: RawStudy, output_name: str) -> None:
        """
        Delete output folder
        Args:
            metadata: study
            output_name: output simulation

        Returns:

        """
        output_path = self.get_study_path(metadata) / "output" / output_name
        shutil.rmtree(output_path, ignore_errors=True)

    def edit_study(
        self, metadata: RawStudy, url: str, new: SUB_JSON
    ) -> SUB_JSON:
        """
        Replace data on disk with new
        Args:
            metadata: study
            url: data path to reach
            new: new data to replace

        Returns: new data replaced

        """
        # Get data
        self.check_study_exists(metadata)

        study_path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(study_path, metadata.id)
        study.save(new, url.split("/"))  # type: ignore
        del study
        return new
