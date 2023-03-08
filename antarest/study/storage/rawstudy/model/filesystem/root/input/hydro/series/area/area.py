from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_hourly,
    default_scenario_daily,
    default_scenario_monthly,
    MatrixFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputHydroSeriesArea(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "mod": InputSeriesMatrix(
                self.context,
                self.config.next_file("mod.txt"),
                default_empty=default_scenario_daily
                if self.config.version >= 650
                else default_scenario_monthly,
                freq=MatrixFrequency.DAILY
                if self.config.version >= 650
                else MatrixFrequency.MONTHLY,
            ),
            "ror": InputSeriesMatrix(
                self.context,
                self.config.next_file("ror.txt"),
                default_empty=default_scenario_hourly,
            ),
        }
        return children
