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

from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateXpansionConstraint(ICommand):
    """
    Command used to create  a matrice in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_XPANSION_CONSTRAINT

    # Command parameters
    # ==================

    filename: str
    data: bytes

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return (
            CommandOutput(
                status=True,
                message=f"Xpansion constraint {self.filename} has been successfully created.",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        study_data.tree.save(data=self.data, url=["user", "expansion", "constraints", self.filename])
        output, _ = self._apply_config(study_data.config)
        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "filename": self.filename,
                "data": self.data,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
