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

import importlib
import itertools
import pkgutil
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class TestCommandFactory:
    # noinspection SpellCheckingInspection
    def setup_class(self):
        """
        Set up the test class.

        Imports all modules from the `antarest.study.storage.variantstudy.model.command` package
        and creates a set of command class names derived from the `ICommand` abstract class.
        The objective is to ensure that the unit test covers all commands in this package.

        This method is executed once before any tests in the test class are run.
        """
        for module_loader, name, ispkg in pkgutil.iter_modules(["antarest/study/storage/variantstudy/model/command"]):
            importlib.import_module(
                f".{name}",
                package="antarest.study.storage.variantstudy.model.command",
            )
        abstract_commands = {"AbstractBindingConstraintCommand"}
        self.command_class_set = {
            cmd.__name__ for cmd in ICommand.__subclasses__() if cmd.__name__ not in abstract_commands
        }

    # noinspection SpellCheckingInspection
    @pytest.mark.parametrize(
        "command_dto",
        [
            CommandDTO(
                action=CommandName.CREATE_AREA.value,
                args={"area_name": "area_name"},
            ),
            CommandDTO(
                action=CommandName.CREATE_AREA.value,
                args=[
                    {"area_name": "area_name"},
                    {"area_name": "area2"},
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_AREA.value,
                args={"id": "id"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_AREA.value,
                args=[{"id": "id"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_DISTRICT.value,
                args={
                    "name": "id",
                    "filter_items": ["a"],
                    "output": True,
                    "comments": "",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_DISTRICT.value,
                args=[
                    {
                        "name": "id",
                        "base_filter": "add-all",
                        "output": True,
                        "comments": "",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_DISTRICT.value,
                args={"id": "id"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_DISTRICT.value,
                args=[{"id": "id"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_LINK.value,
                args={
                    "area1": "area1",
                    "area2": "area2",
                    "parameters": {},
                    "series": "series",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_LINK.value,
                args=[
                    {
                        "area1": "area1",
                        "area2": "area2",
                        "parameters": {},
                        "series": "series",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_LINK.value,
                args={
                    "area1": "area1",
                    "area2": "area2",
                },
            ),
            CommandDTO(
                action=CommandName.REMOVE_LINK.value,
                args=[
                    {
                        "area1": "area1",
                        "area2": "area2",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.CREATE_BINDING_CONSTRAINT.value,
                args={"name": "name"},
            ),
            CommandDTO(
                action=CommandName.CREATE_BINDING_CONSTRAINT.value,
                args=[
                    {
                        "name": "name",
                        "enabled": True,
                        "time_step": "hourly",
                        "operator": "equal",
                        "values": "values",
                        "group": "group_1",
                    },
                ],
            ),
            CommandDTO(
                action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
                args={
                    "id": "id",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "equal",
                    "values": "values",
                },
            ),
            CommandDTO(
                action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
                args=[
                    {
                        "id": "id",
                        "enabled": True,
                        "time_step": "hourly",
                        "operator": "equal",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
                args={"id": "id"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
                args=[{"id": "id"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_THERMAL_CLUSTER.value,
                args={
                    "area_id": "area_name",
                    "cluster_name": "cluster_name",
                    "parameters": {
                        "group": "group",
                        "unitcount": "unitcount",
                        "nominalcapacity": "nominalcapacity",
                        "marginal-cost": "marginal-cost",
                        "market-bid-cost": "market-bid-cost",
                    },
                    "prepro": "prepro",
                    "modulation": "modulation",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_THERMAL_CLUSTER.value,
                args=[
                    {
                        "area_id": "area_name",
                        "cluster_name": "cluster_name",
                        "parameters": {
                            "group": "group",
                            "unitcount": "unitcount",
                            "nominalcapacity": "nominalcapacity",
                            "marginal-cost": "marginal-cost",
                            "market-bid-cost": "market-bid-cost",
                        },
                        "prepro": "prepro",
                        "modulation": "modulation",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_THERMAL_CLUSTER.value,
                args={"area_id": "area_name", "cluster_id": "cluster_name"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_THERMAL_CLUSTER.value,
                args=[{"area_id": "area_name", "cluster_id": "cluster_name"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
                args={
                    "area_id": "area_name",
                    "cluster_name": "cluster_name",
                    "parameters": {
                        "name": "name",
                        "ts-interpretation": "power-generation",
                    },
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
                args=[
                    {
                        "area_id": "area_name",
                        "cluster_name": "cluster_name",
                        "parameters": {
                            "name": "name",
                            "ts-interpretation": "power-generation",
                        },
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
                args={"area_id": "area_name", "cluster_id": "cluster_name"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
                args=[{"area_id": "area_name", "cluster_id": "cluster_name"}],
            ),
            CommandDTO(
                action=CommandName.REPLACE_MATRIX.value,
                args={"target": "target_element", "matrix": "matrix"},
            ),
            CommandDTO(
                action=CommandName.REPLACE_MATRIX.value,
                args=[{"target": "target_element", "matrix": "matrix"}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_CONFIG.value,
                args={"target": "target", "data": {}},
            ),
            CommandDTO(
                action=CommandName.UPDATE_CONFIG.value,
                args=[{"target": "target", "data": {}}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_COMMENTS.value,
                args={"comments": "comments"},
            ),
            CommandDTO(
                action=CommandName.UPDATE_COMMENTS.value,
                args=[{"comments": "comments"}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_FILE.value,
                args={
                    "target": "settings/resources/study",
                    "b64Data": "",
                },
            ),
            CommandDTO(
                action=CommandName.UPDATE_DISTRICT.value,
                args={"id": "id", "filter_items": ["a"]},
            ),
            CommandDTO(
                action=CommandName.UPDATE_DISTRICT.value,
                args=[{"id": "id", "base_filter": "add-all"}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_PLAYLIST.value,
                args=[{"active": True, "items": [1, 3], "reverse": False}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_PLAYLIST.value,
                args={
                    "active": True,
                    "items": [1, 3],
                    "weights": {1: 5.0},
                    "reverse": False,
                },
            ),
            CommandDTO(
                action=CommandName.UPDATE_SCENARIO_BUILDER.value,
                args={
                    "data": {
                        "ruleset test": {
                            "l": {"area1": {"0": 1}},
                            "ntc": {"area1 / area2": {"1": 23}},
                            "t": {"area1": {"thermal": {"1": 2}}},
                        },
                    }
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_ST_STORAGE.value,
                args={
                    "area_id": "area 1",
                    "parameters": {
                        "name": "Storage 1",
                        "group": "Battery",
                        "injectionnominalcapacity": 0,
                        "withdrawalnominalcapacity": 0,
                        "reservoircapacity": 0,
                        "efficiency": 1,
                        "initiallevel": 0,
                        "initialleveloptim": False,
                    },
                    "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                    "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                    "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                    "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
                    "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_ST_STORAGE.value,
                args=[
                    {
                        "area_id": "area 1",
                        "parameters": {
                            "efficiency": 1,
                            "group": "Battery",
                            "initiallevel": 0,
                            "initialleveloptim": False,
                            "injectionnominalcapacity": 0,
                            "name": "Storage 1",
                            "reservoircapacity": 0,
                            "withdrawalnominalcapacity": 0,
                        },
                        "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                        "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                        "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                        "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
                        "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
                    },
                    {
                        "area_id": "area 1",
                        "parameters": {
                            "efficiency": 0.94,
                            "group": "Battery",
                            "initiallevel": 0,
                            "initialleveloptim": False,
                            "injectionnominalcapacity": 0,
                            "name": "Storage 2",
                            "reservoircapacity": 0,
                            "withdrawalnominalcapacity": 0,
                        },
                        "pmax_injection": "matrix://3f5b3746-3995-49b7-a6da-622633472e05",
                        "pmax_withdrawal": "matrix://4b64a31f-927b-4887-b4cd-adcddd39bdcd",
                        "lower_rule_curve": "matrix://16c7c3ae-9824-4ef2-aa68-51145884b025",
                        "upper_rule_curve": "matrix://9a6104e9-990a-415f-a6e2-57507e13b58c",
                        "inflows": "matrix://e8923768-9bdd-40c2-a6ea-2da2523be727",
                    },
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_ST_STORAGE.value,
                args={
                    "area_id": "area 1",
                    "storage_id": "storage 1",
                },
            ),
            CommandDTO(
                action=CommandName.REMOVE_ST_STORAGE.value,
                args=[
                    {
                        "area_id": "area 1",
                        "storage_id": "storage 1",
                    },
                    {
                        "area_id": "area 1",
                        "storage_id": "storage 2",
                    },
                ],
            ),
            CommandDTO(
                action=CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES.value,
                args=[{}],
            ),
        ],
    )
    @pytest.mark.unit_test
    def test_command_factory(self, command_dto: CommandDTO):
        def get_matrix_id(matrix: str) -> str:
            # str.removeprefix() is not available in Python 3.8
            prefix = "matrix://"
            if matrix.startswith(prefix):
                return matrix[len(prefix) :]
            return matrix

        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService, get_matrix_id=get_matrix_id),
            patch_service=Mock(spec=PatchService),
        )
        commands = command_factory.to_command(command_dto=command_dto)

        if isinstance(command_dto.args, dict):
            exp_action_args_list = [(command_dto.action, command_dto.args, command_dto.version)]
        else:
            exp_action_args_list = [(command_dto.action, args, command_dto.version) for args in command_dto.args]

        actual_cmd: ICommand
        for actual_cmd, exp_action_args_version in itertools.zip_longest(commands, exp_action_args_list):
            assert actual_cmd is not None, f"Missing action/args for {exp_action_args_version=}"
            assert exp_action_args_version is not None, f"Missing command for {actual_cmd=}"
            expected_action, expected_args, expected_version = exp_action_args_version
            actual_dto = actual_cmd.to_dto()
            actual_args = {k: v for k, v in actual_dto.args.items() if v is not None}
            actual_version = actual_dto.version
            assert actual_dto.action == expected_action
            assert actual_args == expected_args
            assert actual_version == expected_version

        self.command_class_set.discard(type(commands[0]).__name__)

    def teardown_class(self):
        # Check that all command classes have been tested
        assert not self.command_class_set


@pytest.mark.unit_test
def test_unknown_command():
    with pytest.raises(NotImplementedError):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
            patch_service=Mock(spec=PatchService),
        )
        command_factory.to_command(command_dto=CommandDTO(action="unknown_command", args={}))
