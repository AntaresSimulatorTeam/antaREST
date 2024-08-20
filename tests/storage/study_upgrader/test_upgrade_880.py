from antarest.study.storage.study_upgrader import StudyUpgrader
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that short term storages are correctly modified
    """

    # upgrade the study
    study_upgrader = StudyUpgrader(study_assets.study_dir, "880")
    study_upgrader.upgrade()

    # compare st-storage folders (st-storage)
    actual_input_path = study_assets.study_dir / "input" / "st-storage"
    expected_input_path = study_assets.expected_dir / "input" / "st-storage"
    assert are_same_dir(actual_input_path, expected_input_path)
