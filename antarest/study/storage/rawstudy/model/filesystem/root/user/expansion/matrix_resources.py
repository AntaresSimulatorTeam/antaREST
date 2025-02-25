# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class ExpansionMatrixResources(BucketNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config, None, default_file_node=InputSeriesMatrix)

    @override
    def build(self) -> TREE:
        children: TREE = {}
        for resource in self.config.path.iterdir():
            if resource.is_file():
                # Removes the .link suffix if the matrix is normalized
                file_name = resource.name.removesuffix(".link")
                children[file_name] = InputSeriesMatrix(self.context, self.config.next_file(file_name))

        return children
