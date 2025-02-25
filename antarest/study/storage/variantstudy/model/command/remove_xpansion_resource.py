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
import contextlib
from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.core.exceptions import FileCurrentlyUsedInSettings
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


def _is_constraints_file_used(file_study: FileStudy, filename: str) -> bool:
    with contextlib.suppress(KeyError):
        constraints = file_study.tree.get(["user", "expansion", "settings", "additional-constraints"])
        if str(constraints) == filename:
            return True
    return False


def _is_weights_file_used(file_study: FileStudy, filename: str) -> bool:
    with contextlib.suppress(KeyError):
        weights = file_study.tree.get(["user", "expansion", "settings", "yearly-weights"])
        if str(weights) == filename:
            return True
    return False


def _is_capa_file_used(file_study: FileStudy, filename: str) -> bool:
    candidates = file_study.tree.get(["user", "expansion", "candidates"])
    all_link_profiles = [candidate.get("link-profile", None) for candidate in candidates.values()]
    all_link_profiles += [candidate.get("already-installed-link-profile", None) for candidate in candidates.values()]
    return filename in all_link_profiles


def get_resource_dir(resource_type: XpansionResourceFileType) -> List[str]:
    if resource_type == XpansionResourceFileType.CONSTRAINTS:
        return ["user", "expansion", "constraints"]
    elif resource_type == XpansionResourceFileType.CAPACITIES:
        return ["user", "expansion", "capa"]
    elif resource_type == XpansionResourceFileType.WEIGHTS:
        return ["user", "expansion", "weights"]
    raise NotImplementedError(f"resource_type '{resource_type}' not implemented")


def checks_resource_deletion_is_allowed(
    resource_type: XpansionResourceFileType, filename: str, study_data: FileStudy
) -> None:
    file_checkers = {
        XpansionResourceFileType.CONSTRAINTS: _is_constraints_file_used,
        XpansionResourceFileType.CAPACITIES: _is_capa_file_used,
        XpansionResourceFileType.WEIGHTS: _is_weights_file_used,
    }

    if resource_type in file_checkers and file_checkers[resource_type](study_data, filename):
        raise FileCurrentlyUsedInSettings(resource_type, filename)


class RemoveXpansionResource(ICommand):
    """
    Command used to delete a xpansion related resource
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_XPANSION_RESOURCE

    # Command parameters
    # ==================

    resource_type: XpansionResourceFileType
    filename: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message=f"Xpansion resource {self.filename} removed successfully"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        checks_resource_deletion_is_allowed(self.resource_type, self.filename, study_data)

        study_data.tree.delete(get_resource_dir(self.resource_type) + [self.filename])

        return self._apply_config(study_data.config)[0]

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"resource_type": self.resource_type.value, "filename": self.filename},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
