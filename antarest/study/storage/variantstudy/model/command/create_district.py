from typing import Dict

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class CreateDistrict(ICommand):
    id: str
    metadata: Dict[str, str]

    def __init__(self):
        super().__init__(command_name=CommandName.CREATE_DISTRICT, version=1)

    def apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
