from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.links.item.item import (
    OutputSimulationModeMcAllLinksItem as Item,
)


class _OutputSimulationModeMcAllLinksBis(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {}
        for link in self.config.get_links(self.area):
            name = f"{self.area} - {link}"
            children[link] = Item(
                self.context, self.config.next_file(name), self.area, link
            )
        return children


class OutputSimulationModeMcAllLinks(FolderNode):
    def build(self) -> TREE:
        children: TREE = {}

        for area in self.config.area_names():
            children[area] = _OutputSimulationModeMcAllLinksBis(
                self.context, self.config, area
            )

        return children
