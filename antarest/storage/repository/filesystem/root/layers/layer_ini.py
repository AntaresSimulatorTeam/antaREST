from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class LayersIni(IniFileNode):
    """
    Examples
    -------
    [layers]
    0 = All
    1 = Map 1
    [activeLayer]
    activeLayerID = 0
    showAllLayer = true
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            "layers": {},
            "activeLayer": {"activeLayerID": int, "showAllLayer": bool},
        }
        IniFileNode.__init__(self, context, config, types=types)
