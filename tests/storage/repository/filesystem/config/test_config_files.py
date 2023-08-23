from pathlib import Path
from typing import Any, Dict
from zipfile import ZipFile

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    _parse_links,
    _parse_outputs,
    _parse_sets,
    _parse_st_storage,
    _parse_thermal,
    build,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    BindingConstraintDTO,
    Cluster,
    DistrictSet,
    FileStudyTreeConfig,
    Link,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageConfig, STStorageGroup
from antarest.study.storage.variantstudy.model.command.common import TimeStep
from tests.storage.business.assets import ASSETS_DIR


def build_empty_files(tmp: Path) -> Path:
    study_path = tmp / "my-study"
    (study_path / "input/bindingconstraints/").mkdir(parents=True)
    (study_path / "input/bindingconstraints/bindingconstraints.ini").touch()

    (study_path / "input/areas").mkdir(parents=True)
    (study_path / "input/areas/list.txt").touch()
    (study_path / "input/areas/sets.ini").touch()

    (study_path / "input/links").mkdir(parents=True)
    (study_path / "input/thermal/clusters").mkdir(parents=True)

    (study_path / "settings").mkdir(parents=True)
    (study_path / "settings/generaldata.ini").touch()

    return study_path


def test_parse_output_parameters(tmp_path: Path) -> None:
    study = build_empty_files(tmp_path)
    content = """
    [output]
    synthesis = true
    storenewset = true
    archives =
    """
    (study / "settings/generaldata.ini").write_text(content)

    config = FileStudyTreeConfig(
        study_path=study,
        path=study,
        version=-1,
        store_new_set=True,
        study_id="id",
        output_path=study / "output",
    )
    assert build(study, "id") == config


def test_parse_bindings(tmp_path: Path) -> None:
    # Setup files
    study_path = build_empty_files(tmp_path)
    content = """
    [bindA]
    id = bindA
    
    [bindB]
    id = bindB
    """
    (study_path / "input/bindingconstraints/bindingconstraints.ini").write_text(content)

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        version=-1,
        bindings=[
            BindingConstraintDTO(id="bindA", areas=[], clusters=[], time_step=TimeStep.HOURLY),
            BindingConstraintDTO(id="bindB", areas=[], clusters=[], time_step=TimeStep.HOURLY),
        ],
        study_id="id",
        output_path=study_path / "output",
    )

    assert build(study_path, "id") == config


def test_parse_outputs(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    output_path = study_path / "output/20201220-1456eco-hello/"
    output_path.mkdir(parents=True)

    (output_path / "about-the-study").mkdir()
    file = output_path / "about-the-study/parameters.ini"
    content = """
    [general]
    nbyears = 1
    year-by-year = true
    user-playlist = true
    
    [output]
    synthesis = true
    
    [playlist]
    playlist_year + = 0
    """
    file.write_text(content)

    (output_path / "checkIntegrity.txt").touch()

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="id",
        version=-1,
        output_path=study_path / "output",
        outputs={
            "20201220-1456eco-hello": Simulation(
                name="hello",
                date="20201220-1456",
                mode="economy",
                nbyears=1,
                synthesis=True,
                by_year=True,
                error=False,
                playlist=[1],
                xpansion="",
            )
        },
    )
    assert build(study_path, "id") == config


@pytest.mark.parametrize(
    "assets_name, expected",
    [
        (
            "test_output_zip_not_zipped.zip",
            {
                "20230127-1550eco": Simulation(
                    name="",
                    date="20230127-1550",
                    mode="economy",
                    nbyears=1,
                    synthesis=True,
                    by_year=False,
                    error=False,
                    playlist=[],
                    archived=False,
                    xpansion="",
                ),
                "20230203-1530eco": Simulation(
                    name="",
                    date="20230203-1530",
                    mode="economy",
                    nbyears=1,
                    synthesis=False,
                    by_year=False,
                    error=False,
                    playlist=[],
                    archived=False,
                    xpansion="1.0.2",
                ),
                "20230203-1531eco": Simulation(
                    name="",
                    date="20230203-1531",
                    mode="economy",
                    nbyears=1,
                    synthesis=False,
                    by_year=False,
                    error=False,
                    playlist=[],
                    archived=True,
                    xpansion="",
                ),
                "20230203-1600eco": Simulation(
                    name="",
                    date="20230203-1600",
                    mode="economy",
                    nbyears=1,
                    synthesis=True,
                    by_year=False,
                    error=True,
                    playlist=[],
                    archived=False,
                    xpansion="",
                ),
            },
        ),
    ],
)
def test_parse_outputs__nominal(tmp_path: Path, assets_name: str, expected: Dict[str, Any]) -> None:
    """
    This test decompresses a zipped study (stored in the `assets` directory)
    into a temporary directory and executes the parsing of the outputs.
    The result of the analysis is checked to match the expected output data.
    """
    pkg_dir = ASSETS_DIR.joinpath(assets_name)
    with ZipFile(pkg_dir) as zf:
        zf.extractall(tmp_path)
    output_path = tmp_path.joinpath("output")
    actual = _parse_outputs(output_path)
    assert actual == expected


def test_parse_sets(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    content = """
[hello]
output = true
+ = a
+ = b
"""
    (study_path / "input/areas/sets.ini").write_text(content)

    assert _parse_sets(study_path) == {"hello": DistrictSet(areas=["a", "b"], output=True, inverted_set=False)}


def test_parse_area(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/areas/list.txt").write_text("FR\n")
    (study_path / "input/areas/fr").mkdir(parents=True)
    content = """
    [filtering]
    filter-synthesis = daily, monthly
    filter-year-by-year = hourly, weekly, annual
    """
    (study_path / "input/areas/fr/optimization.ini").write_text(content)

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="id",
        version=-1,
        output_path=study_path / "output",
        areas={
            "fr": Area(
                name="FR",
                thermals=[],
                renewables=[],
                links={},
                filters_year=["hourly", "weekly", "annual"],
                filters_synthesis=["daily", "monthly"],
            )
        },
    )
    assert build(study_path, "id") == config


def test_parse_thermal(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/thermal/clusters/fr").mkdir(parents=True)
    content = """
    [t1]
    name = t1
    
    [t2]
    name = t2
    enabled = false

    [t3]
    name = t3
    enabled = true
    """
    (study_path / "input/thermal/clusters/fr/list.ini").write_text(content)

    assert _parse_thermal(study_path, "fr") == [
        Cluster(id="t1", name="t1", enabled=True),
        Cluster(id="t2", name="t2", enabled=False),
        Cluster(id="t3", name="t3", enabled=True),
    ]


# noinspection SpellCheckingInspection
ST_STORAGE_LIST_INI = """\
[siemens battery]
name = Siemens Battery
group = Battery
injectionnominalcapacity = 150.0
withdrawalnominalcapacity = 150.0
reservoircapacity = 600.0
efficiency = 0.94
initiallevel = 0
initialleveloptim = True

[grand maison]
name = Grand'Maison
group = PSP_closed
injectionnominalcapacity = 1500.0
withdrawalnominalcapacity = 1800.0
reservoircapacity = 20000.0
efficiency = 0.78
initiallevel = 10000.0
initialleveloptim = False
"""


def test_parse_st_storage(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    study_path.joinpath("study.antares").write_text("[antares] \n version = 860")
    config_dir = study_path.joinpath("input", "st-storage", "clusters", "fr")
    config_dir.mkdir(parents=True)
    config_dir.joinpath("list.ini").write_text(ST_STORAGE_LIST_INI)
    # noinspection SpellCheckingInspection
    assert _parse_st_storage(study_path, "fr") == [
        STStorageConfig(
            id="siemens battery",
            name="Siemens Battery",
            group=STStorageGroup.BATTERY,
            injection_nominal_capacity=150.0,
            withdrawal_nominal_capacity=150.0,
            reservoir_capacity=600.0,
            efficiency=0.94,
            initial_level=0.0,
            initial_level_optim=True,
        ),
        STStorageConfig(
            id="grand maison",
            name="Grand'Maison",
            group=STStorageGroup.PSP_CLOSED,
            injection_nominal_capacity=1500.0,
            withdrawal_nominal_capacity=1800.0,
            reservoir_capacity=20000.0,
            efficiency=0.78,
            initial_level=10000.0,
            initial_level_optim=False,
        ),
    ]

    # With a study version anterior to 860, it should always return an empty list
    study_path.joinpath("study.antares").write_text("[antares] \n version = 850")
    assert _parse_st_storage(study_path, "fr") == []


def test_parse_st_storage_with_no_file(tmp_path: Path) -> None:
    assert _parse_st_storage(tmp_path, "") == []


def test_parse_links(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/links/fr").mkdir(parents=True)
    content = """
    [l1]
    filter-synthesis = annual
    filter-year-by-year = hourly
    """
    (study_path / "input/links/fr/properties.ini").write_text(content)

    link = Link(filters_synthesis=["annual"], filters_year=["hourly"])
    assert _parse_links(study_path, "fr") == {"l1": link}
