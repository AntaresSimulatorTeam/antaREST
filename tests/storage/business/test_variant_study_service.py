import datetime
import os
import re
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import (
    StudyNotFoundError,
)
from antarest.core.interfaces.cache import CacheConstants
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.utils import get_default_workspace_path
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
    VariantStudySnapshot,
)
from antarest.study.storage.variantstudy.variant_snapshot_generator import (
    SNAPSHOT_RELATIVE_PATH,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


def build_config(study_path: Path):
    return Config(
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=study_path)
            }
        )
    )


@pytest.mark.unit_test
def test_get(tmp_path: str, project_path) -> None:
    """
    path_to_studies
    |_study1 (d)
    |_ study2.py
        |_ settings (d)
    |_myfile (f)
    """

    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()

    data = {"titi": 43}
    sub_route = "settings"

    path = path_study / "settings"
    key = "titi"

    study = Mock()
    study.get.return_value = data
    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        exporter_service=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id="study2.py", path=str(path_study))
    study_service.exists = Mock()
    study_service.exists.return_value = True
    output = study_service.get(metadata=metadata, url=sub_route, depth=2)

    assert output == data

    study.get.assert_called_once_with(["settings"], depth=2, formatted=True)


@pytest.mark.unit_test
def test_get_cache(tmp_path: str) -> None:

    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()
    path = path_study / "settings"

    data = {"titi": 43}
    study = Mock()
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)

    cache = Mock()
    cache.get.return_value = None

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        exporter_service=Mock(),
        config=Mock(),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id="study2.py", path=str(path_study))

    cache_id = f"{metadata.id}/{CacheConstants.RAW_STUDY}"
    study_service.exists = Mock()
    study_service.exists.return_value = True

    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)
    cache.put.assert_called_with(cache_id, data)

    cache.get.return_value = data
    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)


@pytest.mark.unit_test
def test_check_errors():
    study = Mock()
    study.check_errors.return_value = ["Hello"]

    factory = Mock()
    factory.create_from_fs.return_value = None, study
    config = build_config(Path())

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=factory,
        exporter_service=Mock(),
        config=config,
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(
        id="study2.py", path=str(get_default_workspace_path(config) / "study")
    )

    study_service.exists = Mock()
    study_service.exists.return_value = True
    assert study_service.check_errors(metadata) == ["Hello"]


@pytest.mark.unit_test
def test_assert_study_exist(tmp_path: str, project_path) -> None:
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study.antares").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()
    (path_study2 / "study.antares").touch()
    # Input
    study_name = "study2.py"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        exporter_service=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id=study_name, path=str(path_study2))

    study_service.exists = Mock()
    study_service.exists.return_value = True
    study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_assert_study_not_exist(tmp_path: str, project_path) -> None:
    # Create folders
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "myfile").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()

    # Input
    study_name = "study3"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        exporter_service=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id=study_name, path=str(path_study2))

    study_service.exists = Mock()
    study_service.exists.return_value = False

    with pytest.raises(StudyNotFoundError):
        study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_copy_study(
    tmp_path: str,
    clean_ini_writer: Callable,
) -> None:
    path_studies = Path(tmp_path)
    source_name = "study1"
    path_study = path_studies / source_name
    path_study.mkdir()
    snapshot_path = path_studies / source_name / SNAPSHOT_RELATIVE_PATH
    snapshot_path.mkdir()
    path_study_info = snapshot_path / "study.antares"
    path_study_info.touch()

    value = {
        "antares": {
            "caption": "ex1",
            "created": 1480683452,
            "lastsave": 1602678639,
            "author": "unknown",
        },
    }

    study = Mock()
    study.get.return_value = value
    study_factory = Mock()

    config = Mock()
    study_factory.create_from_fs.return_value = config, study
    study_factory.create_from_config.return_value = study

    url_engine = Mock()
    url_engine.resolve.return_value = None, None, None
    config = build_config(path_studies)

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        exporter_service=Mock(),
        config=config,
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    src_md = VariantStudy(id=source_name, path=str(path_study))

    md = study_service.copy(src_md, "dest_name")
    md_id = md.id
    assert str(md.path) == f"{tmp_path}{os.sep}{md_id}"
    study.get.assert_called_once_with(["study"])


@pytest.mark.unit_test
def test_delete_study(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    cache = Mock()

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        exporter_service=Mock(),
        config=build_config(tmp_path),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    md = VariantStudy(id=name, path=str(study_path))

    study_service.delete(md)
    cache.invalidate_all.assert_called_once_with(
        [
            f"{name}/{CacheConstants.RAW_STUDY}",
            f"{name}/{CacheConstants.STUDY_FACTORY}",
        ]
    )
    assert not study_path.exists()


@pytest.mark.unit_test
def test_edit_study(tmp_path: Path) -> None:
    # Mock
    (tmp_path / "my-uuid").mkdir()
    (tmp_path / "my-uuid/snapshot/").mkdir()
    (tmp_path / "my-uuid/snapshot/study.antares").touch()

    study = Mock()
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    cache = Mock()
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        exporter_service=Mock(),
        config=build_config(tmp_path),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    # Input
    url = "url/to/change"
    new = {"Hello": "World"}

    id = "my-uuid"
    now = datetime.datetime.now()
    md = VariantStudy(
        id=id,
        path=str(tmp_path / "my-uuid"),
        updated_at=now,
        snapshot=VariantStudySnapshot(id=id, created_at=now),
    )

    res = study_service.edit_study(md, url, new)
    cache.invalidate_all.assert_called_once_with(
        [
            f"{id}/{CacheConstants.RAW_STUDY}",
            f"{id}/{CacheConstants.STUDY_FACTORY}",
        ]
    )
    assert new == res
    study.save.assert_called_once_with(new, ["url", "to", "change"])
