from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.study_antares import (
    StudyAntares,
)


class OutputSimulationAboutStudy(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=StudyAntares.json_validator
        )
