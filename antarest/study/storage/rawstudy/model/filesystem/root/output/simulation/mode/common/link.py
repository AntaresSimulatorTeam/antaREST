from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import LinkOutputSeriesMatrix


class OutputSimulationLinkItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        link: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.link = link

    def build(self) -> TREE:
        children: TREE = {}
        possible_outputs = ["id", "values"]
        freq: MatrixFrequency
        for freq in MatrixFrequency:
            for output_type in possible_outputs:
                file_name = f"{output_type}-{freq}.txt"
                if (self.config.path / file_name).exists():
                    children[f"{output_type}-{freq}"] = LinkOutputSeriesMatrix(
                        self.context,
                        self.config.next_file(file_name),
                        freq,
                        self.area,
                        self.link,
                    )

        return children
