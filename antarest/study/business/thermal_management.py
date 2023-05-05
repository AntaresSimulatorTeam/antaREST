import json
from enum import Enum

from pydantic import Field

from antarest.study.business.utils import (
    FormFieldsBaseModel,
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

    class Config:
        # Allow direct conversion from INI values
        allow_population_by_field_name = True

    # fmt: off
    group: str = ""
    name: str = ""  # fixme: what is the purpose of that field
    unit_count: int = 0
    enabled: bool = True
    nominal_capacity: int = 0
    gen_ts: TimeSeriesGenerationOption = TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER
    min_stable_power: int = 0
    min_up_time: int = 1
    min_down_time: int = 1
    must_run: bool = False
    spinning: float = Field(0.0, description="Spinning (%)", ge=0, le=100)
    volatility_forced: int = 0
    volatility_planned: int = 0
    law_forced: LawOption = LawOption.UNIFORM
    law_planned: LawOption = LawOption.UNIFORM
    marginal_cost: int = 0
    spread_cost: int = 0
    fixed_cost: int = 0
    startup_cost: int = 0
    market_bid_cost: int = 0

    co2: float = Field(0.0, description="Emission rate of CO2 (t/MWh)", ge=0)
    nh3: float = Field(0.0, description="Emission rate of NH3 (t/MWh)", ge=0)
    so2: float = Field(0.0, description="Emission rate of SO2 (t/MWh)", ge=0)
    nox: float = Field(0.0, description="Emission rate of NOX (t/MWh)", ge=0)
    pm2_5: float = Field(0.0, description="Emission rate of PM 2.5 (t/MWh)", ge=0, alias="pm25")
    pm5: float = Field(0.0, description="Emission rate of PM 5 (t/MWh)", ge=0)
    pm10: float = Field(0.0, description="Emission rate of PM 10 (t/MWh)", ge=0)
    nmvoc: float = Field(0.0, description="Emission rate of NMVOC (t/MWh)", ge=0)
    op1: float = Field(0.0, description="Emission rate of pollutant 1 (t/MWh)", ge=0)
    op2: float = Field(0.0, description="Emission rate of pollutant 2 (t/MWh)", ge=0)
    op3: float = Field(0.0, description="Emission rate of pollutant 3 (t/MWh)", ge=0)
    op4: float = Field(0.0, description="Emission rate of pollutant 4 (t/MWh)", ge=0)
    op5: float = Field(0.0, description="Emission rate of pollutant 5 (t/MWh)", ge=0)
    # fmt: on


THERMAL_PATH = "input/thermal/clusters/{area}/list/{cluster}"


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
            THERMAL_PATH.format(area=area_id, cluster=cluster_id).split("/"),
            depth=1,
        )
        # Spinning (%)
        thermal_config["spinning"] = thermal_config.get("spinning", 0) * 100
        return ThermalFormFields.construct(**thermal_config)

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
        # NOTE: The form field names are in camelCase,
        # while the configuration field names are in snake_case.
        thermal_config = json.loads(field_values.json(by_alias=False))
        # Spinning (%)
        thermal_config["spinning"] = thermal_config["spinning"] / 100
        command = UpdateConfig(
            target=THERMAL_PATH.format(area=area_id, cluster=cluster_id),
            data=thermal_config,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
