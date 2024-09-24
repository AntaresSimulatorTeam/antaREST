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

import numpy as np
import pytest
from pydantic import ValidationError

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink, LinkProperties
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateLink:
    def test_validation(self, empty_study: FileStudy, command_context: CommandContext):
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        area2 = "Area2"

        CreateArea.model_validate(
            {
                "area_name": area1,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.model_validate(
            {
                "area_name": area2,
                "command_context": command_context,
            }
        ).apply(empty_study)

        with pytest.raises(ValidationError):
            CreateLink(
                area1=area1_id,
                area2=area1_id,
                parameters={},
                command_context=command_context,
                series=[[0]],
            )

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        study_path = empty_study.config.study_path
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        area3 = "Area3"
        area3_id = transform_name_to_id(area3)

        CreateArea.model_validate(
            {
                "area_name": area1,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.model_validate(
            {
                "area_name": area2,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.model_validate(
            {
                "area_name": area3,
                "command_context": command_context,
            }
        ).apply(empty_study)

        create_link_command: ICommand = CreateLink(
            area1=area1_id,
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status

        assert (study_path / "input" / "links" / area1_id / f"{area2_id}.txt.link").exists()

        link = IniReader()
        link_data = link.read(study_path / "input" / "links" / area1_id / "properties.ini")
        assert link_data[area2_id]["hurdles-cost"] is False
        assert link_data[area2_id]["loop-flow"] is False
        assert  link_data[area2_id]["use-phase-shifter"] is False
        assert link_data[area2_id]["transmission-capacities"] == "enabled"
        assert link_data[area2_id]["asset-type"] == "ac"
        assert link_data[area2_id]["link-style"] == "plain"
        assert int(link_data[area2_id]["link-width"]) == 1
        assert int(link_data[area2_id]["colorr"]) == 112
        assert int(link_data[area2_id]["colorg"]) == 112
        assert int(link_data[area2_id]["colorb"]) == 112
        assert link_data[area2_id]["display-comments"] is True

        empty_study.config.version = 820
        create_link_command: ICommand = CreateLink(
            area1=area2_id,
            area2=area3_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )
        assert output.status
        empty_study.config.version = 800

        assert (study_path / "input" / "links" / area2_id / f"{area3_id}_parameters.txt.link").exists()
        assert (study_path / "input" / "links" / area2_id / "capacities" / f"{area3_id}_direct.txt.link").exists()
        assert (study_path / "input" / "links" / area2_id / "capacities" / f"{area3_id}_indirect.txt.link").exists()

        # TODO:assert matrix default content : 1 column, 8760 rows, value = 1

        output = CreateLink.model_validate(
            {
                "area1": area1_id,
                "area2": area2_id,
                "parameters": {},
                "series": [[0]],
                "command_context": command_context,
            }
        ).apply(study_data=empty_study)

        assert not output.status

        parameters = {
            "hurdles_cost": True,
            "loop_flow": True,
            "use_phase_shifter": True,
            "transmission_capacities": "ignore",
            "asset_type": "dc",
            "link_style": "other",
            "link_width": 12,
            "colorr": 120,
            "colorg": 120,
            "colorb": 120,
            "display_comments": True,
            "filter_synthesis": "hourly",
            "filter_year_by_year": "hourly",
        }

        create_link_command: ICommand = CreateLink.model_validate(
            {
                "area1": area3_id,
                "area2": area1_id,
                "parameters": parameters,
                "series": [[0]],
                "command_context": command_context,
            }
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status

        assert (study_path / "input" / "links" / area1_id / f"{area3_id}.txt.link").exists()

        link = IniReader()
        link_data = link.read(study_path / "input" / "links" / area1_id / "properties.ini")
        assert link_data[area3_id]["hurdles-cost"] == parameters["hurdles_cost"]
        assert link_data[area3_id]["loop-flow"] == parameters["loop_flow"]
        assert link_data[area3_id]["use-phase-shifter"] == parameters["use_phase_shifter"]
        assert link_data[area3_id]["transmission-capacities"] == parameters["transmission_capacities"]
        assert link_data[area3_id]["asset-type"] == parameters["asset_type"]
        assert link_data[area3_id]["link-style"] == parameters["link_style"]
        assert int(link_data[area3_id]["link-width"]) == parameters["link_width"]
        assert int(link_data[area3_id]["colorr"]) == parameters["colorr"]
        assert int(link_data[area3_id]["colorg"]) == parameters["colorg"]
        assert int(link_data[area3_id]["colorb"]) == parameters["colorb"]
        assert link_data[area3_id]["display-comments"] == parameters["display_comments"]

        output = create_link_command.apply(
            study_data=empty_study,
        )
        assert not output.status

        output = CreateLink(
            area1="does_not_exist",
            area2=area2_id,
            parameters={},
            series=[[0]],
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    base = CreateLink(area1="foo", area2="bar", series=[[0]], command_context=command_context)
    other_match = CreateLink(area1="foo", area2="bar", series=[[0]], command_context=command_context)
    other_not_match = CreateLink(area1="foo", area2="baz", command_context=command_context)
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_link%foo%bar"
    # check the matrices links
    matrix_id = command_context.matrix_service.create([[0]])
    assert base.get_inner_matrices() == [matrix_id]


def test_revert(command_context: CommandContext):
    base = CreateLink(area1="foo", area2="bar", series=[[0]], command_context=command_context)
    assert CommandReverter().revert(base, [], None) == [
        RemoveLink(
            area1="foo",
            area2="bar",
            command_context=command_context,
        )
    ]


def test_create_diff(command_context: CommandContext):
    series_a = np.random.rand(8760, 8).tolist()
    base = CreateLink(
        area1="foo",
        area2="bar",
        series=series_a,
        command_context=command_context,
    )

    series_b = np.random.rand(8760, 8).tolist()
    other_match = CreateLink(
        area1="foo",
        area2="bar",
        parameters={"hurdles_cost": "true"},
        series=series_b,
        command_context=command_context,
    )

    assert base.create_diff(other_match) == [
        UpdateConfig(
            target="input/links/bar/properties/foo",
            data=LinkProperties.model_validate({"hurdles_cost": "true"}).model_dump(by_alias=True, exclude_none=True),
            command_context=command_context,
        ),
        ReplaceMatrix(
            target="@links_series/bar/foo",
            matrix=series_b,
            command_context=command_context,
        ),
    ]
