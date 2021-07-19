from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.hydro.hydro import (
    OutputSimulationTsNumbersHydro,
)
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.load.load import (
    OutputSimulationTsNumbersLoad,
)
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.solar.solar import (
    OutputSimulationTsNumbersSolar,
)
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.thermal.thermal import (
    OutputSimulationTsNumbersThermal,
)
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.wind.wind import (
    OutputSimulationTsNumbersWind,
)


class OutputSimulationTsNumbers(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "hydro": OutputSimulationTsNumbersHydro(
                self.context, config.next_file("hydro")
            ),
            "load": OutputSimulationTsNumbersLoad(
                self.context, config.next_file("load")
            ),
            "solar": OutputSimulationTsNumbersSolar(
                self.context, config.next_file("solar")
            ),
            "wind": OutputSimulationTsNumbersWind(
                self.context, config.next_file("wind")
            ),
            "thermal": OutputSimulationTsNumbersThermal(
                self.context, config.next_file("thermal")
            ),
        }
        return children
