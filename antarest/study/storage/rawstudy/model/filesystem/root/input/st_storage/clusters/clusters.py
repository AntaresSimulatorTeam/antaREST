from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.area.area import (
    InputShortTermStorageArea,
)


class InputShortTermStorageClusters(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: InputShortTermStorageArea(
                self.context, self.config.next_file(a), area=a
            )
            for a in self.config.area_names()
        }
        return children
