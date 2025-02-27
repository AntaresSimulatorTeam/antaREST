# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import copy
import logging
import typing as t
from abc import ABCMeta

from antares.study.version import StudyVersion
from pydantic import model_validator
from typing_extensions import override

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    DEFAULT_GROUP,
    OPERATOR_MATRIX_FILE_MAP,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintDTO, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly as default_bc_hourly_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_86,
)
from antarest.study.storage.variantstudy.model.command.binding_constraint_utils import remove_bc_from_scenario_builder
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    BindingConstraintProperties,
    create_binding_constraint_props,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import update_matrices_names
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class UpdateBindingConstraints(ICommand, metaclass=ABCMeta):
    """
    Command used to update a binding constraint.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINTS
    version: int = 1

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    bc_props_by_id: t.Mapping[str, BindingConstraintProperties]
    study_version: StudyVersion

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        for i, existing_constraint in enumerate(study_data.bindings):
            bc_props = self.bc_props_by_id[existing_constraint.id]
            bc_props_as_dict = bc_props.model_dump(mode="json", by_alias=True, exclude_unset=True)
            areas_set = existing_constraint.areas
            clusters_set = existing_constraint.clusters
            group = bc_props_as_dict.get("group") or existing_constraint.group
            operator = bc_props_as_dict.get("operator") or existing_constraint.operator
            time_step = bc_props_as_dict.get("time_step") or existing_constraint.time_step
            new_constraint = BindingConstraintDTO(
                id=existing_constraint.id,
                group=group,
                areas=areas_set,
                clusters=clusters_set,
                operator=operator,
                time_step=time_step,
            )
            study_data.bindings[i] = new_constraint
        return CommandOutput(status=True), {}

    @model_validator(mode="before")
    @classmethod
    def check_version_consistency(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """
        Retrieves the binding constraint configuration class based on the study version.
        """
        bc_by_id = values.get("bc_props_by_id")
        bc_by_id = t.cast(t.Mapping[str, t.Mapping[str, t.Any]], bc_by_id)
        study_version = values.get("study_version")
        study_version = t.cast(StudyVersion, study_version)
        # bcs_props =  bc_props_by_id.values()
        # required_bc_props_cls = get_binding_constraint_config_cls(study_version)
        # input_bc_props = create_binding_constraint_config(study_version, **bc_input_as_dict)

        bc_props_by_id = {
            key: create_binding_constraint_props(study_version, **value) for key, value in bc_by_id.items()
        }

        # for bc_prop in bcs_props:
        #     if not isinstance(bc_prop, required_bc_props_cls):
        #         raise ConstraintVersionDoesNotMatchBindingVersion()
        values["bc_props_by_id"] = bc_props_by_id
        return values

    @override
    def _apply(self, file_study: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        study_version = file_study.config.version
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        dict_config = {value["id"]: key for (key, value) in config.items()}
        # next_bc_props_by_id = {}
        old_groups = set()
        new_groups = set()
        for bc_id, bc_props in self.bc_props_by_id.items():
            if bc_id not in dict_config:
                return CommandOutput(
                    status=False,
                    message=f"Binding contraint '{bc_id}' not found.",
                )
            bc_props_as_dict = bc_props.model_dump(mode="json", by_alias=True, exclude_unset=True)
            bc = config[dict_config[bc_id]]
            bc_copy = copy.deepcopy(bc)
            bc.update(bc_props_as_dict)
            if "time_step" in bc_props_as_dict and bc_props.time_step != BindingConstraintFrequency(bc_copy["type"]):
                # The user changed the time step, we need to update the matrix accordingly
                for [target, next_matrix] in self.generate_replacement_matrices(
                    bc_id, study_version, bc_props, bc_props.operator
                ):
                    matrix_url = target.split("/")
                    replace_matrix_data: JSON = {}
                    target_matrix = replace_matrix_data
                    for element in matrix_url[:-1]:
                        target_matrix[element] = {}
                        target_matrix = target_matrix[element]
                    target_matrix[matrix_url[-1]] = next_matrix
                    file_study.tree.save(replace_matrix_data)
            if (
                "operator" in bc_props_as_dict
                and bc_props.operator != bc_copy["operator"]
                and study_version >= STUDY_VERSION_8_7
            ):
                # The user changed the operator, we have to rename matrices accordingly
                existing_operator = BindingConstraintOperator(bc_copy["operator"])
                update_matrices_names(file_study, bc_id, existing_operator, bc_props.operator)
            if self.study_version >= STUDY_VERSION_8_7:
                old_groups.add(bc_copy.get("group", DEFAULT_GROUP).lower())
                new_groups.add(bc_props_as_dict.get("group", DEFAULT_GROUP).lower())

        removed_groups = old_groups - new_groups
        remove_bc_from_scenario_builder(file_study, removed_groups)

        study_file_target = "input/bindingconstraints/bindingconstraints"
        url = study_file_target.split("/")
        tree_node = file_study.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {study_file_target} is invalid",
            )
        file_study.tree.save(config, url)

        return CommandOutput(status=True, message="ok")

    @override
    def to_dto(self) -> CommandDTO:
        excluded_fields = set(ICommand.model_fields)
        json_command = self.model_dump(mode="json", exclude=excluded_fields, exclude_unset=True)
        return CommandDTO(
            action=self.command_name.value, args=json_command, version=self.version, study_version=self.study_version
        )

    def generate_replacement_matrices(
        self,
        bc_id: str,
        study_version: StudyVersion,
        value: BindingConstraintProperties,
        operator: BindingConstraintOperator,
    ) -> t.Iterator[t.Tuple[str, t.Union[t.List[t.List[MatrixData]], str]]]:
        if study_version < STUDY_VERSION_8_7:
            target = f"input/bindingconstraints/{bc_id}"
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly_86,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_86,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_86,
            }[value.time_step].tolist()
            yield (target, matrix)
        else:
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly_87,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_87,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_87,
            }[value.time_step].tolist()
            matrices_to_replace = OPERATOR_MATRIX_FILE_MAP[operator]
            for matrix_name in matrices_to_replace:
                matrix_id = matrix_name.format(bc_id=bc_id)
                target = f"input/bindingconstraints/{matrix_id}"
                yield (target, matrix)

    @override
    def get_inner_matrices(self) -> t.List[str]:
        """
        Useless here but must implement this function.
        """
        return []
