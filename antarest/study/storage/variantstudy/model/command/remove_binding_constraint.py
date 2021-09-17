from typing import Any, List, Optional

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.command_group import (
    CommandGroup,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.variant_command_extractor import (
    VariantCommandsExtractor,
)


class RemoveBindingConstraint(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_BINDING_CONSTRAINT,
            version=1,
            **data,
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        if self.id not in study_data.config.bindings:
            return CommandOutput(
                status=False, message="Binding constraint not found"
            )

        binding_constraints = study_data.tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
        new_binding_constraints: JSON = {}
        index = 0
        for bd in binding_constraints:
            if binding_constraints[bd]["id"] == self.id:
                continue
            new_binding_constraints[str(index)] = binding_constraints[bd]
            index += 1

        study_data.tree.save(
            new_binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )
        study_data.tree.delete(["input", "bindingconstraints", self.id])
        study_data.config.bindings.remove(self.id)
        return CommandOutput(status=True)

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
            args={
                "id": self.id,
            },
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveBindingConstraint):
            return False
        return self.id == other.id

    def revert(self, history: List["ICommand"], base: FileStudy) -> "ICommand":
        for command in reversed(history):
            if (
                isinstance(command, CreateBindingConstraint)
                and transform_name_to_id(command.name) == self.id
            ):
                return command
        return CommandGroup(
            command_list=VariantCommandsExtractor(
                self.command_context.matrix_service
            ).extract_binding_constraint(base, self.id),
            command_context=self.command_context,
        )
