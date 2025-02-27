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

from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import AreaHeadWriter, LinkHeadWriter


def test_area():
    writer = AreaHeadWriter(area="de", data_type="va", freq="hourly")
    assert writer.build(var=3, start=2, end=4) == "DE\tarea\tva\thourly\n\tVARIABLES\tBEGIN\tEND\n\t3\t2\t4\n\n"


def test_link():
    writer = LinkHeadWriter(src="de", dest="fr", freq="hourly")
    assert writer.build(var=3, start=2, end=4) == "DE\tlink\tva\thourly\nFR\tVARIABLES\tBEGIN\tEND\n\t3\t2\t4\n\n"
