import logging
import re
import tempfile
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, cast
from zipfile import ZipFile

from antarest.core.model import JSON
from antarest.study.common.utils import extract_file_to_tmp_dir
from antarest.study.storage.rawstudy.io.reader import (
    IniReader,
    MultipleSameKeysIniReader,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Simulation,
    Link,
    DistrictSet,
    transform_name_to_id,
    Cluster,
    BindingConstraintDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)

logger = logging.getLogger(__name__)


class FileType(Enum):
    TXT = "txt"
    SIMPLE_INI = "simple_ini"
    MULTI_INI = "multi_ini"


class FileTypeNotSupportedException(Exception):
    pass


class ConfigPathBuilder:
    """
    Fetch information need by StudyConfig from filesystem data
    """

    @staticmethod
    def build(
        study_path: Path, study_id: str, output_path: Optional[Path] = None
    ) -> "FileStudyTreeConfig":
        """
        Extract data from filesystem to build config study.
        Args:
            study_path: study_path with files inside.
            study_id: uuid of the study
            output_path: output_path if not in study_path/output

        Returns: study config fill with data

        """
        (sns, asi, enr_modelling) = ConfigPathBuilder._parse_parameters(
            study_path
        )

        study_path_without_zip_extension = study_path.parent / study_path.stem

        return FileStudyTreeConfig(
            study_path=study_path,
            output_path=output_path or study_path / "output",
            path=study_path_without_zip_extension,
            study_id=study_id,
            version=ConfigPathBuilder._parse_version(study_path),
            areas=ConfigPathBuilder._parse_areas(study_path),
            sets=ConfigPathBuilder._parse_sets(study_path),
            outputs=ConfigPathBuilder._parse_outputs(
                output_path or study_path / "output"
            ),
            bindings=ConfigPathBuilder._parse_bindings(study_path),
            store_new_set=sns,
            archive_input_series=asi,
            enr_modelling=enr_modelling,
            zip_path=study_path if study_path.suffix == ".zip" else None,
        )

    @staticmethod
    def _extract_data_from_file(
        root: Path,
        inside_root_path: Path,
        file_type: FileType,
        multi_ini_keys: Optional[List[str]] = None,
    ) -> Any:
        tmp_dir = None
        if root.suffix == ".zip":
            output_data_path, tmp_dir = extract_file_to_tmp_dir(
                root, inside_root_path
            )
        else:
            output_data_path = root / inside_root_path

        try:
            if file_type == FileType.TXT:
                output_data: Any = output_data_path.read_text().split("\n")
            elif file_type == FileType.MULTI_INI:
                output_data = MultipleSameKeysIniReader(multi_ini_keys).read(
                    output_data_path
                )
            elif file_type == FileType.SIMPLE_INI:
                output_data = IniReader().read(output_data_path)
            else:
                raise FileTypeNotSupportedException()
        except Exception as e:
            logger.error(
                f"Failed to extract data from {root/inside_root_path}",
                exc_info=e,
            )
            output_data = None
        finally:
            if tmp_dir:
                tmp_dir.cleanup()

        return output_data

    @staticmethod
    def _parse_version(path: Path) -> int:
        study_info = ConfigPathBuilder._extract_data_from_file(
            root=path,
            inside_root_path=Path("study.antares"),
            file_type=FileType.SIMPLE_INI,
        )
        version: int = study_info.get("antares", {}).get("version", -1)
        return version

    @staticmethod
    def _parse_parameters(path: Path) -> Tuple[bool, List[str], str]:
        general = ConfigPathBuilder._extract_data_from_file(
            root=path,
            inside_root_path=Path("settings/generaldata.ini"),
            file_type=FileType.MULTI_INI,
        )

        store_new_set: bool = general.get("output", {}).get(
            "storenewset", False
        )
        archive_input_series: List[str] = [
            e.strip()
            for e in general.get("output", {})
            .get("archives", "")
            .strip()
            .split(",")
            if e.strip()
        ]
        enr_modelling: str = general.get("other preferences", {}).get(
            "renewables-generation-modelling", "aggregated"
        )
        return store_new_set, archive_input_series, enr_modelling

    @staticmethod
    def _parse_bindings(root: Path) -> List[BindingConstraintDTO]:
        bindings = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path(
                "input/bindingconstraints/bindingconstraints.ini"
            ),
            file_type=FileType.SIMPLE_INI,
        )
        output_list = []
        for id, bind in bindings.items():
            area_set = set()
            cluster_set = (
                set()
            )  # contains a list of strings in the following format: "area.cluster"
            for key in bind.keys():
                if "%" in key:
                    areas = key.split("%")
                    area_set.add(areas[0])
                    area_set.add(areas[1])
                elif "." in key:
                    cluster_set.add(key)
                    area_set.add(key.split(".")[0])

            output_list.append(
                BindingConstraintDTO(
                    id=bind["id"], areas=area_set, clusters=cluster_set
                )
            )

        return output_list

    @staticmethod
    def _parse_sets(root: Path) -> Dict[str, DistrictSet]:
        json = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path("input/areas/sets.ini"),
            file_type=FileType.MULTI_INI,
            multi_ini_keys=["+", "-"],
        )
        return {
            name.lower(): DistrictSet(
                areas=item.get(
                    "-"
                    if item.get("apply-filter", "remove-all") == "add-all"
                    else "+"
                ),
                name=item.get("caption"),
                inverted_set=item.get("apply-filter", "remove-all")
                == "add-all",
                output=item.get("output", True),
            )
            for name, item in json.items()
        }

    @staticmethod
    def _parse_areas(root: Path) -> Dict[str, Area]:
        areas = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path("input/areas/list.txt"),
            file_type=FileType.TXT,
        )
        areas = [a for a in areas if a != ""]
        return {
            transform_name_to_id(a): ConfigPathBuilder.parse_area(root, a)
            for a in areas
        }

    @staticmethod
    def _parse_outputs(output_path: Path) -> Dict[str, Simulation]:
        if not output_path.exists():
            return {}

        files = sorted(output_path.iterdir())
        sims = {
            f.stem: ConfigPathBuilder.parse_simulation(f)
            for i, f in enumerate(files)
            if (f / "about-the-study").exists() or f.suffix == ".zip"
        }
        return {k: v for k, v in sims.items() if v}

    @staticmethod
    def parse_simulation(path: Path) -> Optional["Simulation"]:
        modes = {"eco": "economy", "adq": "adequacy"}
        regex: Any = re.search(
            "^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)", path.stem
        )
        try:
            if path.suffix == ".zip":
                zf = ZipFile(path, "r")
                error = str("checkIntegrity.txt") not in zf.namelist()
            else:
                error = not (path / "checkIntegrity.txt").exists()
            (
                nbyears,
                by_year,
                synthesis,
                playlist,
            ) = ConfigPathBuilder._parse_outputs_parameters(path)
            return Simulation(
                date=regex.group(1),
                mode=modes[regex.group(2)],
                name=regex.group(3),
                nbyears=nbyears,
                by_year=by_year,
                synthesis=synthesis,
                error=error,
                playlist=playlist,
                archived=path.suffix == ".zip",
            )
        except Exception as e:
            logger.warning(
                f"Failed to parse simulation found at {path}", exc_info=e
            )
        return None

    @staticmethod
    def get_playlist(config: JSON) -> Optional[List[int]]:
        general_config = config.get("general", {})
        nb_years = cast(int, general_config.get("nbyears"))
        playlist_activated = cast(
            bool, general_config.get("user-playlist", False)
        )
        if not playlist_activated:
            return None
        playlist_config = config.get("playlist", {})
        playlist_reset = playlist_config.get("playlist_reset", True)
        added = playlist_config.get("playlist_year +", [])
        removed = playlist_config.get("playlist_year -", [])
        if playlist_reset:
            return [
                year + 1 for year in range(0, nb_years) if year not in removed
            ]
        return [year + 1 for year in added if year not in removed]

    @staticmethod
    def _parse_outputs_parameters(
        path: Path,
    ) -> Tuple[int, bool, bool, Optional[List[int]]]:
        parameters_path_inside_output = "about-the-study/parameters.ini"
        full_path_parameters = path / parameters_path_inside_output
        tmp_dir = None

        if path.suffix == ".zip":
            tmp_dir = tempfile.TemporaryDirectory()
            with ZipFile(path, "r") as zip_obj:
                zip_obj.extract(parameters_path_inside_output, tmp_dir.name)
                full_path_parameters = (
                    Path(tmp_dir.name) / parameters_path_inside_output
                )

        par: JSON = MultipleSameKeysIniReader(DUPLICATE_KEYS).read(
            full_path_parameters
        )

        if tmp_dir:
            tmp_dir.cleanup()

        return (
            par["general"]["nbyears"],
            par["general"]["year-by-year"],
            par["output"]["synthesis"],
            ConfigPathBuilder.get_playlist(par),
        )

    @staticmethod
    def parse_area(root: Path, area: str) -> "Area":
        area_id = transform_name_to_id(area)
        return Area(
            name=area,
            links=ConfigPathBuilder._parse_links(root, area_id),
            thermals=ConfigPathBuilder._parse_thermal(root, area_id),
            renewables=ConfigPathBuilder._parse_renewables(root, area_id),
            filters_synthesis=ConfigPathBuilder._parse_filters_synthesis(
                root, area_id
            ),
            filters_year=ConfigPathBuilder._parse_filters_year(root, area_id),
        )

    @staticmethod
    def _parse_thermal(root: Path, area: str) -> List[Cluster]:
        list_ini = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path(f"input/thermal/clusters/{area}/list.ini"),
            file_type=FileType.SIMPLE_INI,
        )
        return [
            Cluster(
                id=transform_name_to_id(key),
                enabled=list_ini.get(key, {}).get("enabled", True),
                name=list_ini.get(key, {}).get("name", key),
            )
            for key in list(list_ini.keys())
        ]

    @staticmethod
    def _parse_renewables(root: Path, area: str) -> List[Cluster]:
        try:
            list_ini = ConfigPathBuilder._extract_data_from_file(
                root=root,
                inside_root_path=Path(
                    f"input/renewables/clusters/{area}/list.ini"
                ),
                file_type=FileType.SIMPLE_INI,
            )
            return [
                Cluster(
                    id=transform_name_to_id(key),
                    enabled=list_ini.get(key, {}).get("enabled", True),
                    name=list_ini.get(key, {}).get("name", None),
                )
                for key in list(list_ini.keys())
            ]
        except:
            return []

    @staticmethod
    def _parse_links(root: Path, area: str) -> Dict[str, Link]:
        properties_ini = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path(f"input/links/{area}/properties.ini"),
            file_type=FileType.SIMPLE_INI,
        )
        return {
            link: Link.from_json(properties_ini[link])
            for link in list(properties_ini.keys())
        }

    @staticmethod
    def _parse_filters_synthesis(root: Path, area: str) -> List[str]:
        optimization = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path(f"input/areas/{area}/optimization.ini"),
            file_type=FileType.SIMPLE_INI,
        )
        filters: str = optimization["filtering"]["filter-synthesis"]
        return Link.split(filters)

    @staticmethod
    def _parse_filters_year(root: Path, area: str) -> List[str]:
        optimization = ConfigPathBuilder._extract_data_from_file(
            root=root,
            inside_root_path=Path(f"input/areas/{area}/optimization.ini"),
            file_type=FileType.SIMPLE_INI,
        )
        filters: str = optimization["filtering"]["filter-year-by-year"]
        return Link.split(filters)
