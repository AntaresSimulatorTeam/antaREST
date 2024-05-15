import io
import json
import logging
import re
import tempfile
import typing as t
import zipfile
from enum import Enum
from pathlib import Path

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.exceptions import (
    SimulationParsingError,
    XpansionParsingError,
)
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import extract_filtering
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    BindingConstraintDTO,
    DistrictSet,
    FileStudyTreeConfig,
    Link,
    Simulation,
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableConfigType,
    create_renewable_config,
)
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfigType,
    create_st_storage_config,
)
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import ThermalConfigType, create_thermal_config
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import DUPLICATE_KEYS

logger = logging.getLogger(__name__)


class FileType(Enum):
    TXT = "txt"
    SIMPLE_INI = "simple_ini"
    MULTI_INI = "multi_ini"


def build(study_path: Path, study_id: str, output_path: t.Optional[Path] = None) -> "FileStudyTreeConfig":
    """
    Extracts data from the filesystem to build a study config.

    Args:
        study_path: Path to the study directory or ZIP file containing the study.
        study_id: UUID of the study.
        output_path: Optional path for the output directory.
            If not provided, it will be set to `{study_path}/output`.

    Returns:
        An instance of `FileStudyTreeConfig` filled with the study data.
    """
    is_zip_file = study_path.suffix.lower() == ".zip"

    # Study directory to use if the study is compressed
    study_dir = study_path.with_suffix("") if is_zip_file else study_path
    (sns, asi, enr_modelling) = _parse_parameters(study_path)

    outputs_dir: Path = output_path or study_path / "output"
    return FileStudyTreeConfig(
        study_path=study_path,
        output_path=outputs_dir,
        path=study_dir,
        study_id=study_id,
        version=_parse_version(study_path),
        areas=_parse_areas(study_path),
        sets=_parse_sets(study_path),
        outputs=parse_outputs(outputs_dir),
        bindings=_parse_bindings(study_path),
        store_new_set=sns,
        archive_input_series=asi,
        enr_modelling=enr_modelling,
        zip_path=study_path if is_zip_file else None,
    )


def _extract_text_from_zip(root: Path, posix_path: str) -> t.Sequence[str]:
    """
    Extracts text from a file inside a ZIP archive and returns it as a list of lines.

    Args:
        root: The path to the ZIP archive.
        posix_path: The relative path to the file inside the ZIP archive.

    Returns:
        A list of lines in the file. If the file is not found, an empty list is returned.
    """
    with zipfile.ZipFile(root) as zf:
        try:
            with zf.open(posix_path) as f:
                text = f.read().decode("utf-8")
                return text.splitlines(keepends=False)
        except KeyError:
            return []


def _extract_ini_from_zip(root: Path, posix_path: str, multi_ini_keys: t.Sequence[str] = ()) -> t.Mapping[str, t.Any]:
    """
    Extracts data from an INI file inside a ZIP archive and returns it as a dictionary.

    Args:
        root: The path to the ZIP archive.
        posix_path: The relative path to the file inside the ZIP archive.
        multi_ini_keys: List of keys to use for multi INI files.

    Returns:
        A dictionary of keys/values in the INI file. If the file is not found, an empty dictionary is returned.
    """
    reader = IniReader(multi_ini_keys)
    with zipfile.ZipFile(root) as zf:
        try:
            with zf.open(posix_path) as f:
                buffer = io.StringIO(f.read().decode("utf-8"))
                return reader.read(buffer)
        except KeyError:
            return {}


def _extract_data_from_file(
    root: Path,
    inside_root_path: Path,
    file_type: FileType,
    multi_ini_keys: t.Sequence[str] = (),
) -> t.Any:
    """
    Extract and process data from various types of files.

    Args:
        root: Directory or ZIP file containing the study.
        inside_root_path: Relative path to the file to extract.
        file_type: Type of the file to extract: text, simple INI or multi INI.
        multi_ini_keys: List of keys to use for multi INI files.

    Returns:
        The content of the file, processed according to its type:
        - TXT: list of lines
        - SIMPLE_INI or MULTI_INI: dictionary of keys/values
    """

    is_zip_file: bool = root.suffix.lower() == ".zip"
    posix_path: str = inside_root_path.as_posix()

    if file_type == FileType.TXT:
        # Parse the file as a list of lines, return an empty list if missing.
        if is_zip_file:
            return _extract_text_from_zip(root, posix_path)
        else:
            output_data_path = root / inside_root_path
            try:
                return output_data_path.read_text(encoding="utf-8").splitlines(keepends=False)
            except FileNotFoundError:
                return []

    elif file_type in {FileType.MULTI_INI, FileType.SIMPLE_INI}:
        # Parse the file as a dictionary of keys/values, return an empty dictionary if missing.
        if is_zip_file:
            return _extract_ini_from_zip(root, posix_path, multi_ini_keys=multi_ini_keys)
        else:
            output_data_path = root / inside_root_path
            try:
                reader = IniReader(multi_ini_keys)
                return reader.read(output_data_path)
            except FileNotFoundError:
                return {}

    else:  # pragma: no cover
        raise NotImplementedError(file_type)


def _parse_version(path: Path) -> int:
    study_info = _extract_data_from_file(
        root=path,
        inside_root_path=Path("study.antares"),
        file_type=FileType.SIMPLE_INI,
    )
    version: int = study_info.get("antares", {}).get("version", -1)
    return version


def _parse_parameters(path: Path) -> t.Tuple[bool, t.List[str], str]:
    general = _extract_data_from_file(
        root=path,
        inside_root_path=Path("settings/generaldata.ini"),
        file_type=FileType.MULTI_INI,
    )

    store_new_set: bool = general.get("output", {}).get("storenewset", False)
    archive_input_series: t.List[str] = [
        e.strip() for e in general.get("output", {}).get("archives", "").strip().split(",") if e.strip()
    ]
    enr_modelling: str = general.get("other preferences", {}).get("renewable-generation-modelling", "aggregated")
    return store_new_set, archive_input_series, enr_modelling


def _parse_bindings(root: Path) -> t.List[BindingConstraintDTO]:
    bindings = _extract_data_from_file(
        root=root,
        inside_root_path=Path("input/bindingconstraints/bindingconstraints.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    output_list = []
    for bind in bindings.values():
        area_set = set()
        # contains a set of strings in the following format: "area.cluster"
        cluster_set = set()
        # Default value for time_step
        time_step = BindingConstraintFrequency.HOURLY
        for key in bind:
            if key == "type":
                time_step = BindingConstraintFrequency(bind[key])
            elif "%" in key:
                areas = key.split("%", 1)
                area_set.add(areas[0])
                area_set.add(areas[1])
            elif "." in key:
                cluster_set.add(key)
                area_set.add(key.split(".", 1)[0])

        output_list.append(
            BindingConstraintDTO(id=bind["id"], areas=area_set, clusters=cluster_set, time_step=time_step)
        )

    return output_list


def _parse_sets(root: Path) -> t.Dict[str, DistrictSet]:
    obj = _extract_data_from_file(
        root=root,
        inside_root_path=Path("input/areas/sets.ini"),
        file_type=FileType.MULTI_INI,
        multi_ini_keys=["+", "-"],
    )
    return {
        transform_name_to_id(name): DistrictSet(
            areas=item.get("-" if item.get("apply-filter", "remove-all") == "add-all" else "+"),
            name=item.get("caption"),
            inverted_set=item.get("apply-filter", "remove-all") == "add-all",
            output=item.get("output", True),
        )
        for name, item in obj.items()
    }


def _parse_areas(root: Path) -> t.Dict[str, Area]:
    areas = _extract_data_from_file(
        root=root,
        inside_root_path=Path("input/areas/list.txt"),
        file_type=FileType.TXT,
    )
    areas = [a for a in areas if a != ""]
    return {transform_name_to_id(a): parse_area(root, a) for a in areas}


def parse_outputs(output_path: Path) -> t.Dict[str, Simulation]:
    if not output_path.is_dir():
        return {}
    sims = {}
    # Paths are sorted to have the folders _before_ the ZIP files with the same name.
    for path in sorted(output_path.iterdir()):
        suffix = path.suffix.lower()
        path_name = path.name
        try:
            if suffix == ".tmp" or path_name.startswith("~"):
                continue
            elif suffix == ".zip":
                if path.stem not in sims:
                    if simulation := parse_simulation_zip(path):
                        sims[path.stem] = simulation
            elif (path / "about-the-study/parameters.ini").exists():
                if simulation := parse_simulation(path, canonical_name=path_name):
                    sims[path_name] = simulation
        except SimulationParsingError as exc:
            logger.warning(str(exc), exc_info=True)
    return sims


def parse_simulation_zip(path: Path) -> Simulation:
    xpansion_path = "expansion/out.json"
    ini_path = "about-the-study/parameters.ini"
    integrity_path = "checkIntegrity.txt"
    with tempfile.TemporaryDirectory(dir=path.parent, prefix=f"~{path.stem}-", suffix=".tmp") as output_dir:
        try:
            with zipfile.ZipFile(path) as zf:
                try:
                    zf.extract(ini_path, output_dir)
                except KeyError:
                    raise SimulationParsingError(
                        path,
                        f"Parameters file '{ini_path}' not found",
                    ) from None
                if xpansion_path in zf.namelist():
                    zf.extract(xpansion_path, output_dir)
                if integrity_path in zf.namelist():
                    zf.extract(integrity_path, output_dir)
        except zipfile.BadZipFile as exc:
            raise SimulationParsingError(path, f"Bad ZIP file: {exc}") from exc
        simulation = parse_simulation(Path(output_dir), canonical_name=path.stem)
        simulation.archived = True
        return simulation


def _parse_xpansion_version(path: Path) -> str:
    xpansion_json = path / "expansion" / "out.json"
    try:
        content = xpansion_json.read_text(encoding="utf-8")
        obj = json.loads(content)
        return str(obj["antares_xpansion"]["version"])
    except FileNotFoundError:
        return ""
    except json.JSONDecodeError as exc:
        raise XpansionParsingError(xpansion_json, f"invalid JSON format: {exc}") from exc
    except KeyError as exc:
        raise XpansionParsingError(xpansion_json, f"key '{exc}' not found in JSON object") from exc


_regex_eco_adq = re.compile(r"^(\d{8}-\d{4})(eco|adq)-?(.*)")
match_eco_adq = _regex_eco_adq.match


def parse_simulation(path: Path, canonical_name: str) -> Simulation:
    modes = {"eco": "economy", "adq": "adequacy"}
    match = match_eco_adq(canonical_name)
    if match is None:
        raise SimulationParsingError(
            path,
            reason=f"Filename '{canonical_name}' doesn't match {_regex_eco_adq.pattern}",
        )

    try:
        xpansion = _parse_xpansion_version(path)
    except XpansionParsingError as exc:
        # There is something wrong with Xpansion, let's assume it is not used!
        logger.warning(str(exc), exc_info=True)
        xpansion = ""

    ini_path = path / "about-the-study" / "parameters.ini"
    reader = IniReader(DUPLICATE_KEYS)
    try:
        obj: JSON = reader.read(ini_path)
    except FileNotFoundError:
        raise SimulationParsingError(
            path,
            f"Parameters file '{ini_path.relative_to(path)}' not found",
        ) from None

    error = not (path / "checkIntegrity.txt").exists()
    return Simulation(
        date=match.group(1),
        mode=modes[match.group(2)],
        name=match.group(3),
        nbyears=obj["general"]["nbyears"],
        by_year=obj["general"]["year-by-year"],
        synthesis=obj["output"]["synthesis"],
        error=error,
        playlist=list(get_playlist(obj) or {}),
        archived=False,
        xpansion=xpansion,
    )


def get_playlist(config: JSON) -> t.Optional[t.Dict[int, float]]:
    general_config = config.get("general", {})
    nb_years = t.cast(int, general_config.get("nbyears"))
    playlist_activated = t.cast(bool, general_config.get("user-playlist", False))
    if not playlist_activated:
        return None
    playlist_config = config.get("playlist", {})
    playlist_reset = playlist_config.get("playlist_reset", True)
    added = playlist_config.get("playlist_year +", [])
    removed = playlist_config.get("playlist_year -", [])
    weights = {}
    for year_weight in playlist_config.get("playlist_year_weight", []):
        year_weight_elements = year_weight.split(",")
        weights[int(year_weight_elements[0])] = float(year_weight_elements[1])
    if playlist_reset:
        return {year + 1: weights.get(year, 1) for year in range(nb_years) if year not in removed}
    return {year + 1: weights.get(year, 1) for year in added if year not in removed}


def parse_area(root: Path, area: str) -> "Area":
    """
    Parse an area configuration and extract its filtering configuration.

    Args:
        root: The root directory of the study.
        area: The name of the area to parse.

    Returns:
        The area configuration.
    """
    area_id = transform_name_to_id(area)

    # Parse the optimization INI file to extract the filtering configuration.
    # The file is optional, so we use a default value to avoid a parsing error.
    optimization = _extract_data_from_file(
        root=root,
        inside_root_path=Path(f"input/areas/{area_id}/optimization.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    filtering = optimization.get("filtering", {})
    filter_synthesis = extract_filtering(filtering.get("filter-synthesis", ""))
    filter_year_by_year = extract_filtering(filtering.get("filter-year-by-year", ""))

    return Area(
        name=area,
        links=_parse_links_filtering(root, area_id),
        thermals=_parse_thermal(root, area_id),
        renewables=_parse_renewables(root, area_id),
        filters_synthesis=filter_synthesis,
        filters_year=filter_year_by_year,
        st_storages=_parse_st_storage(root, area_id),
    )


def _parse_thermal(root: Path, area: str) -> t.List[ThermalConfigType]:
    """
    Parse the thermal INI file, return an empty list if missing.
    """
    version = _parse_version(root)
    relpath = Path(f"input/thermal/clusters/{area}/list.ini")
    config_dict: t.Dict[str, t.Any] = _extract_data_from_file(
        root=root, inside_root_path=relpath, file_type=FileType.SIMPLE_INI
    )
    config_list = []
    for section, values in config_dict.items():
        try:
            config_list.append(create_thermal_config(version, **values, id=section))
        except ValueError as exc:
            config_path = root.joinpath(relpath)
            logger.warning(f"Invalid thermal configuration: '{section}' in '{config_path}'", exc_info=exc)
    return config_list


def _parse_renewables(root: Path, area: str) -> t.List[RenewableConfigType]:
    """
    Parse the renewables INI file, return an empty list if missing.
    """

    # Before version 8.1, we only have "Load", "Wind" and "Solar" objects.
    # We can't use renewable clusters.
    version = _parse_version(root)
    if version < 810:
        return []

    # Since version 8.1 of the solver, we can use "renewable clusters" objects.
    relpath = Path(f"input/renewables/clusters/{area}/list.ini")
    config_dict: t.Dict[str, t.Any] = _extract_data_from_file(
        root=root,
        inside_root_path=relpath,
        file_type=FileType.SIMPLE_INI,
    )
    config_list = []
    for section, values in config_dict.items():
        try:
            config_list.append(create_renewable_config(version, **values, id=section))
        except ValueError as exc:
            config_path = root.joinpath(relpath)
            logger.warning(f"Invalid renewable configuration: '{section}' in '{config_path}'", exc_info=exc)
    return config_list


def _parse_st_storage(root: Path, area: str) -> t.List[STStorageConfigType]:
    """
    Parse the short-term storage INI file, return an empty list if missing.
    """

    # st_storage feature exists only since 8.6 version
    version = _parse_version(root)
    if version < 860:
        return []

    relpath = Path(f"input/st-storage/clusters/{area}/list.ini")
    config_dict: t.Dict[str, t.Any] = _extract_data_from_file(
        root=root,
        inside_root_path=relpath,
        file_type=FileType.SIMPLE_INI,
    )
    config_list = []
    for section, values in config_dict.items():
        try:
            config_list.append(create_st_storage_config(version, **values, id=section))
        except ValueError as exc:
            config_path = root.joinpath(relpath)
            logger.warning(f"Invalid short-term storage configuration: '{section}' in '{config_path}'", exc_info=exc)
    return config_list


def _parse_links_filtering(root: Path, area: str) -> t.Dict[str, Link]:
    properties_ini = _extract_data_from_file(
        root=root,
        inside_root_path=Path(f"input/links/{area}/properties.ini"),
        file_type=FileType.SIMPLE_INI,
    )
    links_by_ids = {link_id: Link(**obj) for link_id, obj in properties_ini.items()}
    return links_by_ids


def _check_build_on_solver_tests(test_dir: Path) -> None:
    for antares_path in test_dir.rglob("study.antares"):
        study_path = antares_path.parent
        print(f"Checking '{study_path}'...")
        build(study_path, "test")


if __name__ == "__main__":
    TEST_DIR = Path("~/Projects/antarest_data/studies/Antares_Simulator_Tests_NR").expanduser()
    _check_build_on_solver_tests(TEST_DIR)
