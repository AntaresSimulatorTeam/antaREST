from enum import Enum
from pathlib import PurePosixPath
from typing import Any, List, Dict

from pydantic import confloat

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    FieldInfo,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class TimeSeriesGenerationOption(str, Enum):
    USE_GLOBAL_PARAMETER = "use global parameter"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class LawOption(str, Enum):
    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


class ThermalFormFields(FormFieldsBaseModel):
    """
    Pydantic model representing thermal cluster configuration form fields.
    """

    group: str
    name: str
    unit_count: int
    enabled: bool
    nominal_capacity: int
    gen_ts: TimeSeriesGenerationOption
    min_stable_power: int
    min_up_time: int
    min_down_time: int
    must_run: bool
    spinning: int
    co2: confloat(ge=0)
    nh3: confloat(ge=0)
    so2: confloat(ge=0)
    nox: confloat(ge=0)
    pm2_5: confloat(ge=0)
    pm5: confloat(ge=0)
    pm10: confloat(ge=0)
    nmvoc: confloat(ge=0)
    op1: confloat(ge=0)
    op2: confloat(ge=0)
    op3: confloat(ge=0)
    op4: confloat(ge=0)
    op5: confloat(ge=0)
    volatility_forced: int
    volatility_planned: int
    law_forced: LawOption
    law_planned: LawOption
    marginal_cost: int
    spread_cost: int
    fixed_cost: int
    startup_cost: int
    market_bid_cost: int


THERMAL_PATH = "input/thermal/clusters/{area}/list/{cluster}"


def format_path(path: str, area_id: str, cluster_id: str) -> str:
    return path.format(area=area_id, cluster=cluster_id)


class FieldMetadata:
    """Metadata for a field in the thermal form."""

    def __init__(self, path: str, default_value: Any):
        self.path = path
        self.default_value = default_value


FIELDS_METADATA: List[FieldMetadata] = [
    FieldMetadata("group", ""),
    FieldMetadata("name", ""),
    FieldMetadata("unit_count", 0),
    FieldMetadata("enabled", True),
    FieldMetadata("nominal_capacity", 0),
    FieldMetadata("gen_ts", TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER),
    FieldMetadata("min_stable_power", 0),
    FieldMetadata("min_up_time", 1),
    FieldMetadata("min_down_time", 1),
    FieldMetadata("must_run", False),
    FieldMetadata("spinning", 0),
    FieldMetadata("co2", 0),
    FieldMetadata("nh3", 0),
    FieldMetadata("so2", 0),
    FieldMetadata("nox", 0),
    FieldMetadata("pm2_5", 0),
    FieldMetadata("pm5", 0),
    FieldMetadata("pm10", 0),
    FieldMetadata("nmvoc", 0),
    FieldMetadata("op1", 0),
    FieldMetadata("op2", 0),
    FieldMetadata("op3", 0),
    FieldMetadata("op4", 0),
    FieldMetadata("op5", 0),
    FieldMetadata("volatility_forced", 0),
    FieldMetadata("volatility_planned", 0),
    FieldMetadata("law_forced", LawOption.UNIFORM),
    FieldMetadata("law_planned", LawOption.UNIFORM),
    FieldMetadata("marginal_cost", 0),
    FieldMetadata("spread_cost", 0),
    FieldMetadata("fixed_cost", 0),
    FieldMetadata("startup_cost", 0),
    FieldMetadata("market_bid_cost", 0),
]

FIELDS_INFO: Dict[str, FieldInfo] = {
    # Create a dictionary mapping field names to FieldInfo instances
    field_metadata.path: FieldInfo(
        path=f"{THERMAL_PATH}/{field_metadata.path}",
        default_value=field_metadata.default_value,
    )
    for field_metadata in FIELDS_METADATA
}


class ThermalManager:
    """
    Manage thermal clusters configuration in a study
    """

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_field_values(
        self, study: Study, area_id: str, cluster_id: str
    ) -> ThermalFormFields:
        """
        Get thermal cluster configuration for the given study, area_id, and cluster_id.

        Args:
            study: The study object.
            area_id: The area ID of the thermal cluster.
            cluster_id: The cluster ID of the thermal cluster.

        Returns:
            ThermalFormFields object containing the thermal cluster configuration.
        """

        file_study = self.storage_service.get_storage(study).get_raw(study)
        thermal_config = file_study.tree.get(
            format_path(THERMAL_PATH, area_id, cluster_id).split("/")
        )

        # Create a dictionary of field values using FIELDS_INFO
        field_values = {
            name: thermal_config.get(
                PurePosixPath(info["path"]).name, info["default_value"]
            )
            for name, info in FIELDS_INFO.items()
        }

        return ThermalFormFields.construct(**field_values)

    def set_field_values(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        field_values: ThermalFormFields,
    ) -> None:
        """
        Set thermal cluster configuration for the given study, area_id, and cluster_id.

        Args:
            study: The study object.
            area_id: The area ID of the thermal cluster.
            cluster_id: The cluster ID of the thermal cluster.
            field_values: ThermalFormFields object containing the thermal cluster configuration.
        """

        commands: List[UpdateConfig] = []

        for field_name, value in dict(field_values).items():
            if value is not None:
                info = FIELDS_INFO[field_name]

                commands.append(
                    UpdateConfig(
                        target=format_path(info["path"], area_id, cluster_id),
                        data=value,
                        command_context=self.storage_service.variant_study_service.command_factory.command_context,
                    )
                )

        if commands:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )
