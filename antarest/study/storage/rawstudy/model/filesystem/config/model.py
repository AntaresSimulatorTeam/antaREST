import re
import typing as t
from enum import Enum
from pathlib import Path

from pydantic import Field, root_validator
from pydantic.main import BaseModel

from antarest.core.utils.utils import DTO

from .binding_constraint import BindingConstraintDTO
from .field_validators import extract_filtering
from .renewable import RenewableConfigType
from .st_storage import STStorageConfigType
from .thermal import ThermalConfigType


class ENR_MODELLING(Enum):
    AGGREGATED = "aggregated"
    CLUSTERS = "clusters"


class Link(BaseModel, extra="ignore"):
    """
    Object linked to /input/links/<link>/properties.ini information

    Attributes:
        filters_synthesis: list of filters for synthesis data
        filters_year: list of filters for year-by-year data

    Notes:
        Ignore extra fields, because we only need `filter-synthesis` and `filter-year-by-year`.
    """

    filters_synthesis: t.List[str] = Field(default_factory=list)
    filters_year: t.List[str] = Field(default_factory=list)

    @root_validator(pre=True)
    def validation(cls, values: t.MutableMapping[str, t.Any]) -> t.MutableMapping[str, t.Any]:
        # note: field names are in kebab-case in the INI file
        filters_synthesis = values.pop("filter-synthesis", values.pop("filters_synthesis", ""))
        filters_year = values.pop("filter-year-by-year", values.pop("filters_year", ""))
        values["filters_synthesis"] = extract_filtering(filters_synthesis)
        values["filters_year"] = extract_filtering(filters_year)
        return values


class Area(BaseModel, extra="forbid"):
    """
    Object linked to /input/<area>/optimization.ini information
    """

    name: str
    links: t.Dict[str, Link]
    thermals: t.List[ThermalConfigType]
    renewables: t.List[RenewableConfigType]
    filters_synthesis: t.List[str]
    filters_year: t.List[str]
    # since v8.6
    st_storages: t.List[STStorageConfigType] = []


class DistrictSet(BaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    ALL = ["hourly", "daily", "weekly", "monthly", "annual"]
    name: t.Optional[str] = None
    inverted_set: bool = False
    areas: t.Optional[t.List[str]] = None
    output: bool = True
    filters_synthesis: t.List[str] = ALL
    filters_year: t.List[str] = ALL

    def get_areas(self, all_areas: t.List[str]) -> t.List[str]:
        if self.inverted_set:
            return list(set(all_areas).difference(set(self.areas or [])))
        return self.areas or []


class Simulation(BaseModel):
    """
    Object linked to /output/<simulation_name>/about-the-study/** information
    """

    name: str
    date: str
    mode: str
    nbyears: int
    synthesis: bool
    by_year: bool
    error: bool
    playlist: t.Optional[t.List[int]]
    archived: bool = False
    xpansion: str

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq", "draft": "dft"}
        dash = "-" if self.name else ""
        return f"{self.date}{modes[self.mode]}{dash}{self.name}"


class FileStudyTreeConfig(DTO):
    """
    Root object to handle all study parameters which impact tree structure
    """

    def __init__(
        self,
        study_path: Path,
        path: Path,
        study_id: str,
        version: int,
        output_path: t.Optional[Path] = None,
        areas: t.Optional[t.Dict[str, Area]] = None,
        sets: t.Optional[t.Dict[str, DistrictSet]] = None,
        outputs: t.Optional[t.Dict[str, Simulation]] = None,
        bindings: t.Optional[t.List[BindingConstraintDTO]] = None,
        store_new_set: bool = False,
        archive_input_series: t.Optional[t.List[str]] = None,
        enr_modelling: str = ENR_MODELLING.AGGREGATED.value,
        cache: t.Optional[t.Dict[str, t.List[str]]] = None,
        zip_path: t.Optional[Path] = None,
    ):
        self.study_path = study_path
        self.path = path
        self.study_id = study_id
        self.version = version
        self.output_path = output_path
        self.areas = areas or {}
        self.sets = sets or {}
        self.outputs = outputs or {}
        self.bindings = bindings or []
        self.store_new_set = store_new_set
        self.archive_input_series = archive_input_series or []
        self.enr_modelling = enr_modelling
        self.cache = cache or {}
        self.zip_path = zip_path

    def next_file(self, name: str, is_output: bool = False) -> "FileStudyTreeConfig":
        if is_output and name in self.outputs and self.outputs[name].archived:
            zip_path: t.Optional[Path] = self.path / f"{name}.zip"
        else:
            zip_path = self.zip_path

        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
            path=self.path / name,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            cache=self.cache,
            zip_path=zip_path,
        )

    def at_file(self, filepath: Path) -> "FileStudyTreeConfig":
        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
            path=filepath,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            cache=self.cache,
        )

    def area_names(self) -> t.List[str]:
        return self.cache.get("%areas", list(self.areas.keys()))

    def set_names(self, only_output: bool = True) -> t.List[str]:
        return self.cache.get(
            f"%districts%{only_output}",
            [k for k, v in self.sets.items() if v.output or not only_output],
        )

    def get_thermal_ids(self, area: str) -> t.List[str]:
        """
        Returns a list of thermal cluster IDs for a given area.
        Note that IDs may not be in lower case (but series IDs are).
        """
        return self.cache.get(f"%thermal%{area}%{area}", [th.id for th in self.areas[area].thermals])

    def get_renewable_ids(self, area: str) -> t.List[str]:
        """
        Returns a list of renewable cluster IDs for a given area.
        Note that IDs may not be in lower case (but series IDs are).
        """
        return self.cache.get(f"%renewable%{area}", [r.id for r in self.areas[area].renewables])

    def get_st_storage_ids(self, area: str) -> t.List[str]:
        return self.cache.get(f"%st-storage%{area}", [s.id for s in self.areas[area].st_storages])

    def get_links(self, area: str) -> t.List[str]:
        return self.cache.get(f"%links%{area}", list(self.areas[area].links.keys()))

    def get_filters_synthesis(self, area: str, link: t.Optional[str] = None) -> t.List[str]:
        if link:
            return self.areas[area].links[link].filters_synthesis
        if area in self.sets and self.sets[area].output:
            return self.sets[area].filters_synthesis
        return self.areas[area].filters_synthesis

    def get_filters_year(self, area: str, link: t.Optional[str] = None) -> t.List[str]:
        if link:
            return self.areas[area].links[link].filters_year
        if area in self.sets and self.sets[area].output:
            return self.sets[area].filters_year
        return self.areas[area].filters_year


# Invalid chars was taken from Antares Simulator (C++).
_sub_invalid_chars = re.compile(r"[^a-zA-Z0-9_(),& -]+").sub


def transform_name_to_id(name: str, lower: bool = True) -> str:
    """
    Transform a name into an identifier by replacing consecutive
    invalid characters by a single white space, and then whitespaces
    are striped from both ends.

    Valid characters are `[a-zA-Z0-9_(),& -]` (including space).

    Args:
        name: The name to convert.
        lower: The flag used to turn the identifier in lower case.
    """
    valid_id = _sub_invalid_chars(" ", name).strip()
    return valid_id.lower() if lower else valid_id


class FileStudyTreeConfigDTO(BaseModel):
    study_path: Path
    path: Path
    study_id: str
    version: int
    output_path: t.Optional[Path] = None
    areas: t.Dict[str, Area] = dict()
    sets: t.Dict[str, DistrictSet] = dict()
    outputs: t.Dict[str, Simulation] = dict()
    bindings: t.List[BindingConstraintDTO] = list()
    store_new_set: bool = False
    archive_input_series: t.List[str] = list()
    enr_modelling: str = ENR_MODELLING.AGGREGATED.value
    zip_path: t.Optional[Path] = None

    @staticmethod
    def from_build_config(
        config: FileStudyTreeConfig,
    ) -> "FileStudyTreeConfigDTO":
        return FileStudyTreeConfigDTO.construct(
            study_path=config.study_path,
            path=config.path,
            study_id=config.study_id,
            version=config.version,
            output_path=config.output_path,
            areas=config.areas,
            sets=config.sets,
            outputs=config.outputs,
            bindings=config.bindings,
            store_new_set=config.store_new_set,
            archive_input_series=config.archive_input_series,
            enr_modelling=config.enr_modelling,
            zip_path=config.zip_path,
        )

    def to_build_config(self) -> FileStudyTreeConfig:
        return FileStudyTreeConfig(
            study_path=self.study_path,
            path=self.path,
            study_id=self.study_id,
            version=self.version,
            output_path=self.output_path,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            zip_path=self.zip_path,
        )
