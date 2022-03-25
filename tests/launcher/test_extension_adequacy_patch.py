from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig
from antarest.launcher.extensions.adequacy_patch.extension import (
    AdequacyPatchExtension,
)


def test_hooks(tmp_path: Path):
    study_service = Mock()
    adq_ext = AdequacyPatchExtension(
        study_service, Config(storage=StorageConfig(tmp_dir=tmp_path))
    )
    assert adq_ext.get_name() == AdequacyPatchExtension.EXTENSION_NAME

    study_export_path = tmp_path / "study"
    study_export_path.mkdir()

    study_tree = Mock()
    study_config = Mock()
    filestudy = Mock()
    filestudy.tree = study_tree
    filestudy.config = study_config
    study_service.storage_service.raw_study_service.study_factory.create_from_fs.return_value = (
        filestudy
    )

    study_tree.get.side_effect = [{}, {"flowbased": {}}, '{"areas": []}']

    with pytest.raises(AssertionError):
        adq_ext.after_export_flat_hook(
            "some-job", "some-study-id", study_export_path, {}
        )

    adq_ext.after_export_flat_hook(
        "some-job", "some-study-id", study_export_path, {}
    )
    assert (study_export_path / "post-processing.R").exists()
