import glob
import logging
import re
import shutil
import tempfile
import time
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from typing import Any, Optional

import numpy
import pandas  # type: ignore

from antarest.core.exceptions import (
    StudyValidationError,
    UnsupportedStudyVersion,
)
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)


LOGGER = logging.getLogger(__name__)
OTHER_PREFERENCES = "other preferences"
GENERAL_DATA_PATH = Path("settings") / "generaldata.ini"
ADEQUACY_PATCH = "adequacy patch"
MAPPING_TRANSMISSION_CAPACITIES = {
    True: "local-values",
    False: "null-for-all-links",
    "infinite": "infinite-for-all-links",
}


def modify_file(
    study_path: Path,
    file_path: Path,
    key: str,
    parameter_to_add: Optional[str],
    value: Any,
    parameter_to_delete: Optional[str],
) -> None:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    file = study_path / file_path
    data = reader.read(file)
    if key in data:
        if parameter_to_add is not None:
            data[key][parameter_to_add] = value
        if parameter_to_delete is not None:
            del data[key][parameter_to_delete]
    elif parameter_to_add is not None:
        data[key] = {parameter_to_add: value}
    writer = IniWriter(special_keys=DUPLICATE_KEYS)
    writer.write(data, file)


def find_value_in_file(
    study_path: Path, file_path: Path, key: str, parameter_to_check: str
) -> Any:
    reader = MultipleSameKeysIniReader(DUPLICATE_KEYS)
    file = study_path / file_path
    data = reader.read(file)
    return data[key][parameter_to_check]


def upgrade_700(study_path: Path) -> None:
    # It's the base case study so we pass
    pass


def upgrade_710(study_path: Path) -> None:
    geographical_trimming = find_value_in_file(
        study_path, GENERAL_DATA_PATH, "general", "filtering"
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        "link-type",
        "local",
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "general",
        "geographic-trimming",
        geographical_trimming,
        "filtering",
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "general",
        "thematic-trimming",
        False,
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        OTHER_PREFERENCES,
        "hydro-pricing-mode",
        "fast",
        None,
    )


def upgrade_720(study_path: Path) -> None:
    # There is no input modification between the 7.1.0 and the 7.2.0 version
    pass


def upgrade_800(study_path: Path) -> None:
    custom_ts_numbers_value = find_value_in_file(
        study_path, GENERAL_DATA_PATH, "general", "custom-ts-numbers"
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        OTHER_PREFERENCES,
        "hydro-heuristic-policy",
        "accommodate rule curves",
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        "include-exportstructure",
        False,
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        "include-unfeasible-problem-behavior",
        "error-verbose",
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "general",
        "custom-scenario",
        custom_ts_numbers_value,
        "custom-ts-numbers",
    )


def upgrade_810(study_path: Path) -> None:
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        OTHER_PREFERENCES,
        "renewable-generation-modelling",
        "aggregated",
        None,
    )
    study_path.joinpath("input", "renewables", "clusters").mkdir(parents=True)
    study_path.joinpath("input", "renewables", "series").mkdir(parents=True)

    # TODO Cannot update study with renewables clusters for the moment


def upgrade_820(study_path: Path) -> None:
    links = glob.glob(str(study_path / "input" / "links" / "*"))
    if len(links) > 0:
        for folder in links:
            folder_path = Path(folder)
            all_txt = glob.glob(str(folder_path / "*.txt"))
            if len(all_txt) > 0:
                (folder_path / "capacities").mkdir()
                for txt in all_txt:
                    df = pandas.read_csv(txt, sep="\t", header=None)
                    df_parameters = df.iloc[:, 2:8]
                    df_direct = df.iloc[:, 0]
                    df_indirect = df.iloc[:, 1]
                    name = Path(txt).stem
                    numpy.savetxt(
                        folder_path / f"{name}_parameters.txt",
                        df_parameters.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder_path / "capacities" / f"{name}_direct.txt",
                        df_direct.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    numpy.savetxt(
                        folder_path / "capacities" / f"{name}_indirect.txt",
                        df_indirect.values,
                        delimiter="\t",
                        fmt="%.6f",
                    )
                    (folder_path / f"{name}.txt").unlink()


def upgrade_830(study_path: Path) -> None:
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        "include-split-exported-mps",
        False,
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        ADEQUACY_PATCH,
        "include-adq-patch",
        False,
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        ADEQUACY_PATCH,
        "set-to-null-ntc-between-physical-out-for-first-step",
        True,
        None,
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        ADEQUACY_PATCH,
        "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step",
        True,
        None,
    )
    areas = glob.glob(str(study_path / "input" / "areas" / "*"))
    if len(areas) > 0:
        for folder in areas:
            folder_path = Path(folder)
            if folder_path.is_dir():
                writer = IniWriter()
                writer.write(
                    {"adequacy-patch": {"adequacy-patch-mode": "outside"}},
                    folder_path / "adequacy_patch.ini",
                )


def upgrade_840(study_path: Path) -> None:
    old_value = find_value_in_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        "transmission-capacities",
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        None,
        None,
        "include-split-exported-mps",
    )
    modify_file(
        study_path,
        GENERAL_DATA_PATH,
        "optimization",
        "transmission-capacities",
        MAPPING_TRANSMISSION_CAPACITIES[old_value],
        None,
    )


UPGRADE_METHODS = [
    ("700", "710", upgrade_710),
    ("710", "720", upgrade_720),
    ("720", "800", upgrade_800),
    ("800", "810", upgrade_810),
    ("810", "820", upgrade_820),
    ("820", "830", upgrade_830),
    ("830", "840", upgrade_840),
]


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


def upgrade_study(study_path: Path, target_version: str) -> None:
    tmp_dir = Path(
        tempfile.mkdtemp(
            suffix=".upgrade.tmp", prefix="~", dir=study_path.parent
        )
    )
    shutil.copytree(study_path, tmp_dir, dirs_exist_ok=True)
    try:
        src_version = get_current_version(tmp_dir)
        checks_if_upgrade_is_possible(src_version, target_version)
        do_upgrade(tmp_dir, src_version, target_version)
    except (StudyValidationError, InvalidUpgrade) as e:
        shutil.rmtree(tmp_dir)
        LOGGER.warning(str(e))
        raise
    except UnsupportedStudyVersion as e:
        shutil.rmtree(tmp_dir)
        LOGGER.warning(str(e.detail))
        raise
    except Exception as e:
        shutil.rmtree(tmp_dir)
        LOGGER.error(f"Unhandled exception : {e}", exc_info=True)
        raise
    else:
        backup_dir = Path(
            tempfile.mkdtemp(
                suffix=".backup.tmp", prefix="~", dir=study_path.parent
            )
        )
        backup_dir.rmdir()
        study_path.rename(backup_dir)
        tmp_dir.rename(study_path)
        shutil.rmtree(backup_dir, ignore_errors=True)


def get_current_version(study_path: Path) -> str:
    lines = (study_path / "study.antares").read_text(encoding="utf-8")
    possible_match = re.search(r"^version\s*=\s*(.*)$", lines, flags=re.MULTILINE)
    if possible_match is not None:
        return possible_match[1].rstrip()
    raise StudyValidationError(
        "Your study.antares file is not in the good format"
    )


def checks_if_upgrade_is_possible(src_version: str, dst_version: str) -> None:
    if src_version == dst_version:
        raise InvalidUpgrade(f"Your study is already in version {dst_version}")

    sources = [u[0] for u in UPGRADE_METHODS]
    if src_version not in sources:
        raise InvalidUpgrade(
            f"Version {src_version} unknown: possible versions are {', '.join(sources)}"
        )

    targets = [u[1] for u in UPGRADE_METHODS]
    if dst_version not in targets:
        raise InvalidUpgrade(
            f"Version {dst_version} unknown: possible versions are {', '.join(targets)}"
        )

    curr_version = src_version
    for src, dst in zip(sources, targets):
        if curr_version == src:
            curr_version = dst

    if curr_version != dst_version:
        raise InvalidUpgrade(
            f"Impossible to upgrade from version {src_version} to version {dst_version}"
        )


def update_study_antares_file(target_version: str, study_path: Path) -> None:
    file = study_path / "study.antares"
    content = file.read_text(encoding="utf-8")
    content = re.sub(
        r"^version\s*=.*$",
        f"version = {target_version}",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^lastsave\s*=.*$",
        f"lastsave = {int(time.time())}",
        content,
        flags=re.MULTILINE,
    )
    file.write_text(content, encoding="utf-8")


def do_upgrade(
    study_path: Path, src_version: str, target_version: str
) -> None:
    update_study_antares_file(target_version, study_path)
    curr_version = src_version
    for old, new, method in UPGRADE_METHODS:
        if curr_version == old and curr_version != target_version:
            method(study_path)
            curr_version = new
