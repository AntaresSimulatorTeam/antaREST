from typing import Dict, List, Union, Any, Optional

from pydantic import validator

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import Link
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.default_values import (
    LinkProperties,
    FilteringOptions,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
)


class LinkAlreadyExistError(Exception):
    pass


class CreateLink(ICommand):
    area1: str
    area2: str
    parameters: Dict[str, str]
    series: Optional[Union[List[List[float]], str]] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_LINK, version=1, **data
        )

    @validator("series", always=True)
    def validate_series(
        cls, v: Optional[Union[List[List[float]], str]], values: Any
    ) -> Optional[Union[List[List[float]], str]]:
        if v is None:
            v = values["command_context"].generator_matrix_constants.get_link()
            return v
        else:
            return validate_matrix(v, values)

    def _create_link_in_config(
        self, area_from: str, area_to: str, study_data: FileStudy
    ) -> None:
        study_data.config.areas[area_from].links[area_to] = Link(
            filters_synthesis=[
                step.strip()
                for step in self.parameters.get(
                    "filter-synthesis",
                    FilteringOptions.FILTER_SYNTHESIS.value,
                ).split(",")
            ],
            filters_year=[
                step.strip()
                for step in self.parameters.get(
                    "filter-year-by-year",
                    FilteringOptions.FILTER_YEAR_BY_YEAR.value,
                ).split(",")
            ],
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.area1 not in study_data.config.areas:
            return CommandOutput(
                status=False, message=f"The area '{self.area1}' does not exist"
            )
        if self.area2 not in study_data.config.areas:
            return CommandOutput(
                status=False, message=f"The area '{self.area2}' does not exist"
            )

        if self.area2 in study_data.config.areas[self.area1].links:
            return CommandOutput(
                status=False,
                message=f"The link between {self.area1} and {self.area2} already exist.",
            )
        if self.area1 in study_data.config.areas[self.area2].links:
            return CommandOutput(
                status=False,
                message=f"The link between {self.area1} and {self.area2} already exist.",
            )

        area_from, area_to = sorted([self.area1, self.area2])

        self._create_link_in_config(area_from, area_to, study_data)
        self._create_link_in_config(area_to, area_from, study_data)

        if (
            study_data.config.path
            / "input"
            / "links"
            / area_from
            / f"{area_to}.txt"
        ).exists():
            return CommandOutput(
                status=False,
                message=f"The link between {self.area1} and {self.area2} already exist",
            )

        new_link_data: JSON = {
            "input": {
                "links": {
                    area_from: {
                        "properties": {
                            area_to: {
                                "hurldes-cost": self.parameters.get(
                                    "hurdles-cost",
                                    LinkProperties.HURDLES_COST.value,
                                ),
                                "loop-flow": self.parameters.get(
                                    "loop-flow", LinkProperties.LOOP_FLOW.value
                                ),
                                "use-phase-shifter": self.parameters.get(
                                    "use-phase-shifter",
                                    LinkProperties.USE_PHASE_SHIFTER.value,
                                ),
                                "transmission-capacities": self.parameters.get(
                                    "transmission-capacities",
                                    LinkProperties.TRANSMISSION_CAPACITIES.value,
                                ),
                                "asset-type": self.parameters.get(
                                    "asset-type",
                                    LinkProperties.ASSET_TYPE.value,
                                ),
                                "link-style": self.parameters.get(
                                    "link-style",
                                    LinkProperties.LINK_STYLE.value,
                                ),
                                "link-width": self.parameters.get(
                                    "link-width",
                                    LinkProperties.LINK_WIDTH.value,
                                ),
                                "colorr": self.parameters.get(
                                    "colorr", LinkProperties.COLORR.value
                                ),
                                "colorg": self.parameters.get(
                                    "colorg", LinkProperties.COLORG.value
                                ),
                                "colorb": self.parameters.get(
                                    "colorb", LinkProperties.COLORB.value
                                ),
                                "display-comments": self.parameters.get(
                                    "display-comments",
                                    LinkProperties.DISPLAY_COMMENTS.value,
                                ),
                                "filter-synthesis": self.parameters.get(
                                    "filter-synthesis",
                                    FilteringOptions.FILTER_SYNTHESIS.value,
                                ),
                                "filter-year-by-year": self.parameters.get(
                                    "filter-year-by-year",
                                    FilteringOptions.FILTER_YEAR_BY_YEAR.value,
                                ),
                            }
                        },
                        area_to: self.series,
                    }
                }
            }
        }

        study_data.tree.save(new_link_data)

        return CommandOutput(
            status=True,
            message=f"Link between '{self.area1}' and '{self.area2}' created",
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
