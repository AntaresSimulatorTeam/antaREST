from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.wind.prepro.area.conversion import (
    InputWindPreproAreaConversation,
)
from antarest.storage.repository.filesystem.root.input.wind.prepro.area.data import (
    InputWindPreproAreaData,
)
from antarest.storage.repository.filesystem.root.input.wind.prepro.area.k import (
    InputWindPreproAreaK,
)
from antarest.storage.repository.filesystem.root.input.wind.prepro.area.settings import (
    InputWindPreproAreaSettings,
)
from antarest.storage.repository.filesystem.root.input.wind.prepro.area.translation import (
    InputWindPreproAreaTranslation,
)


class InputWindPreproArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
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
