from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.prepro.area.conversion import (
    InputWindPreproAreaConversation,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.prepro.area.data import (
    InputWindPreproAreaData,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.prepro.area.k import (
    InputWindPreproAreaK,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.prepro.area.settings import (
    InputWindPreproAreaSettings,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.prepro.area.translation import (
    InputWindPreproAreaTranslation,
)


class InputWindPreproArea(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "conversion": InputWindPreproAreaConversation(
                self.context, config.next_file("conversion.txt")
            ),
            "data": InputWindPreproAreaData(
                self.context, config.next_file("data.txt")
            ),
            "k": InputWindPreproAreaK(self.context, config.next_file("k.txt")),
            "translation": InputWindPreproAreaTranslation(
                self.context, config.next_file("translation.txt")
            ),
            "settings": InputWindPreproAreaSettings(
                self.context, config.next_file("settings.ini")
            ),
        }
        return children
