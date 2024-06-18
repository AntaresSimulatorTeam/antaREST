from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.utils import (
    OutputSimulationModeCommon,
)


class OutputSimulationModeMcInd(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        super().__init__(context, config)
        self.simulation = simulation

    def build(self) -> TREE:
        children: TREE = {
            f"{scn:05d}": OutputSimulationModeCommon(self.context, self.config.next_file(f"{scn:05d}"))
            for scn in self.simulation.playlist or range(1, self.simulation.nbyears + 1)
        }
        return children
