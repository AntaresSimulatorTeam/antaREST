# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.link import (
    OutputSimulationLinkItem,
)


class _OutputSimulationModeMcAllLinksBis(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area_from: str,
        link_names: t.List[str],
    ):
        super().__init__(context, config)
        self.area_from = area_from
        self.link_names = link_names

    def build(self) -> TREE:
        children: TREE = {}
        for link_name in self.link_names:
            link = link_name.split(" - ")[1]
            children[link] = OutputSimulationLinkItem(
                self.context, self.config.next_file(link_name), self.area_from, link
            )
        return children


class OutputSimulationLinks(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
    ):
        super().__init__(context, config)

    def build(self) -> TREE:
        children: TREE = {}
        links = [d.stem for d in self.config.path.iterdir()]
        areas: t.Dict[str, t.List[str]] = {}
        for link in links:
            areas.setdefault(link.split(" - ")[0], []).append(link)
        for area_from, link_names in areas.items():
            children[area_from] = _OutputSimulationModeMcAllLinksBis(self.context, self.config, area_from, link_names)

        return children
