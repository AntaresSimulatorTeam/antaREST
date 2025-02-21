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

from antarest.study.business.model.sts_model import STStorageUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
    create_st_storage_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_ST_STORAGE_PATH = "input/st-storage/clusters/{area_id}/list/{storage_id}"


class UpdateSTStorage(ICommand):
    """
    Command used to update a short-term storage in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_ST_STORAGE

    # Command parameters
    # ==================

    area_id: str
    st_storage_id: str
    properties: STStorageUpdate

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        for index, sts in enumerate(study_data.areas[self.area_id].st_storages):
            if sts.id == self.st_storage_id:
                values = sts.model_dump()
                values.update(self.properties.model_dump(exclude_unset=True, exclude_none=True))
                study_data.areas[self.area_id].st_storages[index] = STStorageConfig.model_validate(values)
                break

        return (
            CommandOutput(
                status=True,
                message=f"The st_storage cluster '{self.st_storage_id}' in the area '{self.area_id}' has been updated.",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        path = _ST_STORAGE_PATH.format(area_id=self.area_id, storage_id=self.st_storage_id).split("/")

        current_sts_config = create_st_storage_config(study_version=self.study_version, **study_data.tree.get(path))

        current_properties = current_sts_config.model_dump(exclude={"id"})
        current_properties.update(self.properties.model_dump(exclude_unset=True))

        study_data.tree.save(current_properties, path)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "st_storage_id": self.st_storage_id,
                "properties": self.properties.model_dump(mode="json", exclude_unset=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
