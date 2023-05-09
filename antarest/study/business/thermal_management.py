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
    USE_GLOBAL = "use global"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class LawOption(str, Enum):
    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


# noinspection SpellCheckingInspection
class ThermalFormFields(FormFieldsBaseModel):
    """
    Pydantic model representing thermal cluster configuration form fields.
    """

    class Config:
        # Allow direct conversion from INI values
        allow_population_by_field_name = True

    # https://github.com/AntaresSimulatorTeam/Antares_Simulator/blob/develop/src/libs/antares/study/parts/thermal/cluster.h
    # https://github.com/AntaresSimulatorTeam/Antares_Simulator/blob/develop/src/libs/antares/study/parts/thermal/cluster_list.cpp

    # fmt: off
    group: str = ""
    name: str = ""
    unit_count: int = Field(1, description="Unit count", ge=1, ini_alias="unitcount")
    enabled: bool = Field(True, description="Enable flag")
    nominal_capacity: float = Field(
        0.0, description="Nominal capacity - spinning (MW)", ge=0, ini_alias="nominalcapacity")
    gen_ts: TimeSeriesGenerationOption = Field(
        TimeSeriesGenerationOption.USE_GLOBAL, description="Time Series Generation Option", ini_alias="gen-ts")
    min_stable_power: float = Field(0.0, description="Min. Stable Power (MW)", ini_alias="min-stable-power")
    min_up_time: int = Field(1, description="Min. Uptime (h)", ge=1, le=168, ini_alias="min-up-time")
    min_down_time: int = Field(1, description="Min. Downtime (h)", ge=1, le=168, ini_alias="min-down-time")
    must_run: bool = Field(False, description="Must run flag", ini_alias="must-run")
    spinning: float = Field(0.0, description="Spinning (%)", ge=0, le=100)
    volatility_forced: float = Field(0.0, description="Forced Volatility", ge=0, le=1, ini_alias="volatility.forced")
    volatility_planned: float = Field(0.0, description="Planned volatility", ge=0, le=1, ini_alias="volatility.planned")
    law_forced: LawOption = Field(LawOption.UNIFORM, description="Forced Law (ts-generator)", ini_alias="law.forced")
    law_planned: LawOption = Field(LawOption.UNIFORM, description="Planned Law (ts-generator)", ini_alias="law.planned")
    marginal_cost: float = Field(0.0, description="Marginal cost (euros/MWh)", ge=0, ini_alias="marginal-cost")
    spread_cost: float = Field(0.0, description="Spread (euros/MWh)", ge=0, ini_alias="spread-cost")
    fixed_cost: float = Field(0.0, description="Fixed cost (euros/hour)", ge=0, ini_alias="fixed-cost")
    startup_cost: float = Field(0.0, description="Startup cost (euros/startup)", ge=0, ini_alias="startup-cost")
    market_bid_cost: float = Field(0.0, description="Market bid cost (euros/MWh)", ge=0, ini_alias="market-bid-cost")

    # NOTE: The following fields are deprecated
    # group_min_count: int = Field(0, description="Minimum number of group", ge=0, ini_alias="groupmincount")
    # group_max_count: int = Field(0, description="Maximum number of group", ge=0, ini_alias="groupmaxcount")
    # annuity_investment: int = Field(
    #     0, description="Annuity investment (kEuros/MW)", ge=0, ini_alias="annuityinvestment")

    # https://github.com/AntaresSimulatorTeam/Antares_Simulator/blob/develop/src/libs/antares/study/parts/thermal/pollutant.h

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


class ThermalFieldsNotFoundError(Exception):
    """Fields of the thermal cluster are not found"""


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
        # fmt: off
        try:
            thermal_config = file_study.tree.get(
                THERMAL_PATH.format(area=area_id, cluster=cluster_id).split("/"),
                depth=1,
            )
        except KeyError:
            raise ThermalFieldsNotFoundError(
                f"Fields of thermal cluster '{cluster_id}' not found in '{area_id}'"
            ) from None
        else:
            return ThermalFormFields.from_ini(thermal_config)
        # fmt: on

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
        thermal_config = field_values.to_ini()
        command = UpdateConfig(
            target=THERMAL_PATH.format(area=area_id, cluster=cluster_id),
            data=thermal_config,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
