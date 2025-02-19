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
from typing import List, Optional

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import ThermalPropertiesType
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_THERMAL_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{thermal_cluster_id}"


class UpdateThermalCluster(ICommand):
    """
    Command used to update a short-term storage in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_THERMAL_CLUSTER

    # Command parameters
    # ==================

    area_id: str
    thermal_cluster_id: str
    properties: ThermalPropertiesType

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return (
            CommandOutput(
                status=True,
                message=f"The thermal cluster '{self.thermal_cluster_id}' in the area '{self.area_id}' has been updated.",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        path = _THERMAL_CLUSTER_PATH.format(area_id=self.area_id, thermal_cluster_id=self.thermal_cluster_id)

        study_data.tree.save(self.properties.model_dump(by_alias=True), path.split("/"))

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "thermal_cluster_id": self.thermal_cluster_id,
                "properties": self.properties.model_dump(mode="json"),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
