from typing import Optional, List, Union, Dict, Callable

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


class BucketNode(FolderNode):
    """
    Node to handle structure free, user purpose folder. BucketNode accept any file or sub folder as children.
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        planned_files: Optional[
            Dict[str, Callable[[ContextServer, FileStudyTreeConfig], INode]]
        ] = None,
    ):
        super().__init__(context, config)
        self.planned_files = planned_files or {}

    def save(
        self,
        data: Union[str, int, bool, float, bytes, JSON],
        url: Optional[List[str]] = None,
    ) -> None:
        if url is None or len(url) == 0:
            assert isinstance(data, Dict)
            for key, value in data.items():
                self._save(value, key)
        else:
            key = url[0]
            if len(url) > 1:
                if key in self.planned_files:
                    self.planned_files[key](
                        self.context, self.config.next_file(key)
                    ).save(data, url[1:])
                else:
                    BucketNode(self.context, self.config.next_file(key)).save(
                        data, url[1:]
                    )
            else:
                self._save(data, key)

    def _save(
        self, data: Union[str, int, bool, float, bytes, JSON], key: str
    ) -> None:
        if key in self.planned_files:
            self.planned_files[key](
                self.context, self.config.next_file(key)
            ).save(data)
        if isinstance(data, (str, bytes)):
            RawFileNode(self.context, self.config.next_file(key)).save(data)
        elif isinstance(data, dict):
            BucketNode(self.context, self.config.next_file(key)).save(data)

    def build(self) -> TREE:
        if not self.config.path.exists():
            return dict()

        children: TREE = {}
        for item in sorted(self.config.path.iterdir()):
            if item.name in self.planned_files:
                children[item.name] = self.planned_files[item.name](
                    self.context, self.config.next_file(item.name)
                )
            elif item.is_file():
                children[item.name] = RawFileNode(
                    self.context, self.config.next_file(item.name)
                )
            else:
                children[item.name] = BucketNode(
                    self.context, self.config.next_file(item.name)
                )

        return children

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        return []
