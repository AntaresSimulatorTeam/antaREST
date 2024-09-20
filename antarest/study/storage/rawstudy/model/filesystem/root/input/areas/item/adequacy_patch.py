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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputAreasAdequacyPatch(IniFileNode):
    # Examples
    # --------
    #
    # [adequacy-patch]
    #     adequacy-patch-mode = outside     # outside | inside | virtual
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {"adequacy-patch": {"adequacy-patch-mode": str}}
        IniFileNode.__init__(self, context, config, types)
