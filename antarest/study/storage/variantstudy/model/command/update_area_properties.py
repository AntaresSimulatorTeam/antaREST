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
from typing import Dict, List, Optional

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaFolder, ThermalAreasProperties
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateAreaProperties(ICommand):
    """
    Command used to move an area inside the map and to update its UI.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_AREA_PROPERTIES

    # Command parameters
    # ==================
    list_area_folder: Dict[str, AreaFolder]
    list_thermal_area_properties: List[ThermalAreasProperties]

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True, message=f"area properties updated"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        self.update_thermal_properties(study_data)

        for area_id, area_folder in self.list_area_folder.items():
            self.update_area_optimization(area_id, study_data)
            self.update_adequacy_patch(area_id, study_data)

        output, _ = self._apply_config(study_data.config)

        return output

    def update_thermal_properties(self, study_data: FileStudy) -> None:
        properties = study_data.tree.get(["input", "thermal", "areas"])
        for thermal_area_property in self.list_thermal_area_properties:
            properties["spilledenergycost"].update(thermal_area_property.spilled_energy_cost)
            properties["unserverdenergycost"].update(thermal_area_property.unserverd_energy_cost)
        study_data.tree.save(properties, ["input", "thermal", "areas"])

    def update_adequacy_patch(self, area_id: str, study_data: FileStudy) -> None:
        area_folder = self.list_area_folder.get(area_id)

        if area_folder and area_folder.adequacy_patch:
            new_config = area_folder.adequacy_patch.to_config()
            adequacy_patch_properties = study_data.tree.get(["input", "areas", area_id, "adequacy_patch"])

            if adequacy_patch_properties != new_config:
                adequacy_patch_properties.update(new_config)
                study_data.tree.save(adequacy_patch_properties, ["input", "areas", area_id, "adequacy_patch"])

    def update_area_optimization(self, area_id: str, study_data: FileStudy) -> None:
        area_folder = self.list_area_folder.get(area_id)
        if area_folder is None:
            raise ValueError(f"Aucun AreaFolder trouvé pour l'area_id {area_id}")

        optimization_properties = study_data.tree.get(["input", "areas", area_id, "optimization"])
        new_config = area_folder.optimization.to_config()
        if optimization_properties != new_config:
            optimization_properties.update(new_config)
            study_data.tree.save(optimization_properties, ["input", "areas", area_id, "optimization"])

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREA_PROPERTIES.value,
            args={
                "area_folder": self.list_area_folder,
                "thermal_area_properties": self.list_thermal_area_properties,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
