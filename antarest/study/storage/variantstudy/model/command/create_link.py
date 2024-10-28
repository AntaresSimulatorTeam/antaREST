# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import typing as t
from abc import ABCMeta
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from antares.study.version import StudyVersion
from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated

from antarest.core.exceptions import LinkValidationError
from antarest.core.serialization import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.links import (
    AssetType,
    FilterOption,
    LinkStyle,
    TransmissionCapacity,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Link
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, FilteringOptions
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

DEFAULT_COLOR = 112
MATRIX_ATTRIBUTES = ["series", "direct", "indirect"]
FILTER_VALUES: t.List[FilterOption] = [
    FilterOption.HOURLY,
    FilterOption.DAILY,
    FilterOption.WEEKLY,
    FilterOption.MONTHLY,
    FilterOption.ANNUAL,
]


def validate_filters(
    filter_value: Union[List[FilterOption], str], enum_cls: t.Type[FilterOption]
) -> List[FilterOption]:
    if filter_value is not None and isinstance(filter_value, str):
        filter_accepted_values = [e for e in enum_cls]

        options = filter_value.replace(" ", "").split(",")

        invalid_options = [opt for opt in options if opt not in filter_accepted_values]
        if invalid_options:
            raise LinkValidationError(
                f"Invalid value(s) in filters: {', '.join(invalid_options)}. "
                f"Allowed values are: {', '.join(filter_accepted_values)}."
            )

        return [enum_cls(opt) for opt in options]

    return filter_value


def join_with_comma(values: t.List[FilterOption]) -> str:
    return ", ".join(value.name.lower() for value in values)


class AreaInfo(AntaresBaseModel):
    area1: str
    area2: str


class LinkInfoProperties(AntaresBaseModel):
    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacity = TransmissionCapacity.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    colorr: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    colorb: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    colorg: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    link_width: float = 1
    link_style: LinkStyle = LinkStyle.PLAIN

    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True)


comma_separated_enum_list = Annotated[
    t.List[FilterOption],
    BeforeValidator(lambda x: validate_filters(x, FilterOption)),
    PlainSerializer(lambda x: join_with_comma(x)),
]


class LinkInfoProperties820(LinkInfoProperties):
    filter_synthesis: comma_separated_enum_list = FILTER_VALUES
    filter_year_by_year: comma_separated_enum_list = FILTER_VALUES

    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True)


class LinkProperties(LinkInfoProperties820):
    model_config = ConfigDict(extra="forbid")


class AbstractLinkCommand(ICommand, metaclass=ABCMeta):
    command_name: CommandName

    # Command parameters
    # ==================

    area1: str
    area2: str
    parameters: Optional[Dict[str, Any]] = None
    series: Optional[Union[List[List[MatrixData]], str]] = None
    direct: Optional[Union[List[List[MatrixData]], str]] = None
    indirect: Optional[Union[List[List[MatrixData]], str]] = None

    @field_validator("series", "direct", "indirect", mode="before")
    def validate_series(
        cls, v: Optional[Union[List[List[MatrixData]], str]], values: Union[Dict[str, Any], ValidationInfo]
    ) -> Optional[Union[List[List[MatrixData]], str]]:
        new_values = values if isinstance(values, dict) else values.data
        return validate_matrix(v, new_values) if v is not None else v

    @model_validator(mode="after")
    def validate_areas(self) -> "AbstractLinkCommand":
        if self.area1 == self.area2:
            raise ValueError("Cannot create link on same node")
        return self

    def to_dto(self) -> CommandDTO:
        args = {
            "area1": self.area1,
            "area2": self.area2,
            "parameters": self.parameters,
        }
        for attr in MATRIX_ATTRIBUTES:
            if value := getattr(self, attr, None):
                args[attr] = strip_matrix_protocol(value)
        return CommandDTO(
            action=self.command_name.value,
            args=args,
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateLink):
            return False
        simple_match = self.area1 == other.area1 and self.area2 == other.area2
        if not equal:
            return simple_match
        return (
            simple_match
            and self.parameters == other.parameters
            and self.series == other.series
            and self.direct == other.direct
            and self.indirect == other.indirect
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        other = cast(CreateLink, other)
        from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
        from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

        commands: List[ICommand] = []
        area_from, area_to = sorted([self.area1, self.area2])
        if self.parameters != other.parameters:
            properties = LinkProperties.model_validate(other.parameters or {})
            link_property = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            commands.append(
                UpdateConfig(
                    target=f"input/links/{area_from}/properties/{area_to}",
                    data=link_property,
                    command_context=self.command_context,
                )
            )
        if self.series != other.series:
            commands.append(
                ReplaceMatrix(
                    target=f"@links_series/{area_from}/{area_to}",
                    matrix=strip_matrix_protocol(other.series),
                    command_context=self.command_context,
                )
            )
        return commands

    def get_inner_matrices(self) -> List[str]:
        list_matrices = []
        for attr in MATRIX_ATTRIBUTES:
            if value := getattr(self, attr, None):
                assert_this(isinstance(value, str))
                list_matrices.append(strip_matrix_protocol(value))
        return list_matrices

    def save_series(self, area_from: str, area_to: str, study_data: FileStudy, version: StudyVersion) -> None:
        self.series = self.series or (self.command_context.generator_matrix_constants.get_link(version=version))
        assert isinstance(self.series, str)
        if version < STUDY_VERSION_8_2:
            study_data.tree.save(self.series, ["input", "links", area_from, area_to])
        else:
            study_data.tree.save(
                self.series,
                ["input", "links", area_from, f"{area_to}_parameters"],
            )
            study_data.tree.save({}, ["input", "links", area_from, "capacities"])

    def save_direct(self, area_from: str, area_to: str, study_data: FileStudy, version: StudyVersion) -> None:
        self.direct = self.direct or (self.command_context.generator_matrix_constants.get_link_direct())
        assert isinstance(self.direct, str)
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save({}, ["input", "links", area_from, "capacities"])
            study_data.tree.save(
                self.direct,
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_direct",
                ],
            )

    def save_indirect(self, area_from: str, area_to: str, study_data: FileStudy, version: StudyVersion) -> None:
        self.indirect = self.indirect or (self.command_context.generator_matrix_constants.get_link_indirect())
        assert isinstance(self.indirect, str)
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save({}, ["input", "links", area_from, "capacities"])
            study_data.tree.save(
                self.indirect,
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_indirect",
                ],
            )


class CreateLink(AbstractLinkCommand):
    """
    Command used to create a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_LINK
    version: int = 1

    def _create_link_in_config(self, area_from: str, area_to: str, study_data: FileStudyTreeConfig) -> None:
        self.parameters = self.parameters or {}
        study_data.areas[area_from].links[area_to] = Link(
            filters_synthesis=[
                step.strip()
                for step in self.parameters.get(
                    "filter-synthesis",
                    FilteringOptions.FILTER_SYNTHESIS,
                ).split(",")
            ],
            filters_year=[
                step.strip()
                for step in self.parameters.get(
                    "filter-year-by-year",
                    FilteringOptions.FILTER_YEAR_BY_YEAR,
                ).split(",")
            ],
        )

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area1 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area1}' does not exist",
                ),
                {},
            )
        if self.area2 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area2}' does not exist",
                ),
                {},
            )

        # Link parameters between two areas are stored in only one of the two
        # areas in the "input/links" tree. One area acts as source (`area_from`)
        # and the other as target (`area_to`).
        # Parameters are stored in the target area (`area_to`).
        # The choice as to which area plays the role of source or target is made
        # arbitrarily by sorting the area IDs in lexicographic order.
        # The first will be the source and the second will be the target.
        area_from, area_to = sorted([self.area1, self.area2])
        if area_to in study_data.areas[area_from].links:
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} already exist.",
                ),
                {},
            )

        self._create_link_in_config(area_from, area_to, study_data)

        if (study_data.path / "input" / "links" / area_from / f"{area_to}.txt").exists():
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} already exist",
                ),
                {},
            )

        return (
            CommandOutput(
                status=True,
                message=f"Link between '{self.area1}' and '{self.area2}' created",
            ),
            {"area_from": area_from, "area_to": area_to},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        version = study_data.config.version
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output

        properties: LinkInfoProperties
        if StudyVersion.parse(version) >= STUDY_VERSION_8_2:
            properties = LinkInfoProperties820.model_validate(self.parameters or {})
        else:
            properties = LinkInfoProperties.model_validate(self.parameters or {})

        link_property = properties.model_dump(mode="json", exclude={"area1", "area2"}, by_alias=True, exclude_none=True)

        area_from = data["area_from"]
        area_to = data["area_to"]

        study_data.tree.save(link_property, ["input", "links", area_from, "properties", area_to])

        self.save_series(area_from, area_to, study_data, version)
        self.save_direct(area_from, area_to, study_data, version)
        self.save_indirect(area_from, area_to, study_data, version)

        return output

    def to_dto(self) -> CommandDTO:
        return super().to_dto()

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.area1 + MATCH_SIGNATURE_SEPARATOR + self.area2
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        return super().match(other, equal)

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return super()._create_diff(other)

    def get_inner_matrices(self) -> List[str]:
        return super().get_inner_matrices()
