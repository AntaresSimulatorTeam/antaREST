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

from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    BindingConstraintDTO,
    DistrictSet,
    FileStudyTreeConfig,
    FileStudyTreeConfigDTO,
    Simulation,
)


def test_file_study_tree_config_dto():
    config = FileStudyTreeConfig(
        study_path=Path("test"),
        path=Path("curr_path"),
        study_id="study_id",
        version=700,
        output_path=Path("output_path"),
        areas={
            "a": Area(
                name="a",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
        sets={"s": DistrictSet()},
        outputs={
            "o": Simulation(
                name="o",
                date="date",
                mode="mode",
                nbyears=1,
                synthesis=True,
                by_year=True,
                error=True,
                playlist=[0],
                xpansion="",
            )
        },
        bindings=[
            BindingConstraintDTO(
                id="b1",
                areas=set(),
                clusters=set(),
                time_step=BindingConstraintFrequency.DAILY,
            )
        ],
        store_new_set=False,
        archive_input_series=["?"],
        enr_modelling="aggregated",
    )
    config_dto = FileStudyTreeConfigDTO.from_build_config(config)
    assert sorted(list(config_dto.model_dump()) + ["cache"]) == sorted(list(config.__dict__))
    assert config_dto.to_build_config() == config
