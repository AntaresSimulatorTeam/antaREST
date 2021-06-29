from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.links.item.item import (
    OutputSimulationModeMcIndScnLinksItem as Item,
)


class _OutputSimulationModeMcIndScnLinksBis(FolderNode):
    def __init__(self, context: ContextServer, config: StudyConfig, area: str):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}
        for link in config.get_links(self.area):
            name = f"{self.area} - {link}"
            children[link] = Item(
                self.context, config.next_file(name), self.area, link
            )
        return children


class OutputSimulationModeMcIndScnLinks(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}

        for area in config.area_names():
            children[area] = _OutputSimulationModeMcIndScnLinksBis(
                self.context, config, area
            )

        return children
