from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.prepro.area.conversion import (
    InputLoadPreproAreaConversation,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.prepro.area.data import (
    InputLoadPreproAreaData,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.prepro.area.k import (
    InputLoadPreproAreaK,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.prepro.area.settings import (
    InputLoadPreproAreaSettings,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.prepro.area.translation import (
    InputLoadPreproAreaTranslation,
)


class InputLoadPreproArea(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "conversion": InputLoadPreproAreaConversation(
                self.context, config.next_file("conversion.txt")
            ),
            "data": InputLoadPreproAreaData(
                self.context, config.next_file("data.txt")
            ),
            "k": InputLoadPreproAreaK(self.context, config.next_file("k.txt")),
            "translation": InputLoadPreproAreaTranslation(
                self.context, config.next_file("translation.txt")
            ),
            "settings": InputLoadPreproAreaSettings(
                self.context, config.next_file("settings.ini")
            ),
        }
        return children
