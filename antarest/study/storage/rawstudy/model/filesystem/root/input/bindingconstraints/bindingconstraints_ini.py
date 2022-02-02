from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
    DEFAULT_INI_VALIDATOR,
)


class BindingConstraintsIni(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=DEFAULT_INI_VALIDATOR
        )
