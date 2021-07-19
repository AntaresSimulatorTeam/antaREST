from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.load.prepro.prepro import (
    InputLoadPrepro,
)
from antarest.storage.repository.filesystem.root.input.load.series.series import (
    InputLoadSeries,
)


class InputLoad(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "prepro": InputLoadPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputLoadSeries(
                self.context, config.next_file("series")
            ),
        }
        return children
