from typing import Dict, Any, Union, List, Optional

from antarest.core.custom_types import JSON, SUB_JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateConfig(ICommand):
    target: str
    data: Union[str, int, float, bool, JSON]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_CONFIG, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(self.data, url)
        return CommandOutput(status=True, message="ok")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_CONFIG.value,
            args={
                "target": self.target,
                "data": self.data,
            },
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateConfig):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.data == other.data

    def revert(self, history: List["ICommand"], base: FileStudy) -> "ICommand":
        for command in reversed(history):
            if (
                isinstance(command, UpdateConfig)
                and command.target == self.target
            ):
                return command
        return UpdateConfig(
            target=self.target,
            data=base.tree.get(self.target.split("/")),
            command_context=self.command_context,
        )
