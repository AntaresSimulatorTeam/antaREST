from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.settings.resources.study_ico import (
    StudyIcon,
)


class Resources(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "study": StudyIcon(self.context, config.next_file("study.ico"))
        }
        return children
