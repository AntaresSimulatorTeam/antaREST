from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


class BucketNode(FolderNode):
    """
    Node to handle structure free, user purpose folder. BucketNode accept any file or sub folder as children.
    """

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        for key, value in data.items():
            if isinstance(value, (str, bytes)):
                RawFileNode(self.context, self.config.next_file(key)).save(
                    value  # type: ignore
                )
            elif isinstance(value, dict):
                BucketNode(self.context, self.config.next_file(key)).save(
                    value
                )

    def build(self, config: StudyConfig) -> TREE:
        if not config.path.exists():
            return dict()

        children: TREE = {}
        for item in sorted(config.path.iterdir()):
            if item.is_file():
                children[item.name] = RawFileNode(
                    self.context, config.next_file(item.name)
                )
            else:
                children[item.name] = BucketNode(
                    self.context, config.next_file(item.name)
                )

        return children

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        return []
