from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveArea(ICommand):
    id: str

    def __init__(self):
        super().__init__(command_name="remove_area")

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
