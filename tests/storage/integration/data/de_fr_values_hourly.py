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

import numpy

de_fr_values_hourly = {
    "columns": [
        ("FLOW LIN.", "MWh", ""),
        ("UCAP LIN.", "MWh", ""),
        ("LOOP FLOW", "MWh", ""),
        ("FLOW QUAD.", "MWh", ""),
        ("CONG. FEE (ALG.)", "Euro", ""),
        ("CONG. FEE (ABS.)", "Euro", ""),
        ("MARG. COST", "Euro/MW", ""),
        ("CONG. PROB +", "%", ""),
        ("CONG. PROB -", "%", ""),
        ("HURDLE COST", "Euro", ""),
    ],
    "data": numpy.zeros((168, 10)),
    "index": [
        "01/01 00:00",
        "01/01 01:00",
        "01/01 02:00",
        "01/01 03:00",
        "01/01 04:00",
        "01/01 05:00",
        "01/01 06:00",
        "01/01 07:00",
        "01/01 08:00",
        "01/01 09:00",
        "01/01 10:00",
        "01/01 11:00",
        "01/01 12:00",
        "01/01 13:00",
        "01/01 14:00",
        "01/01 15:00",
        "01/01 16:00",
        "01/01 17:00",
        "01/01 18:00",
        "01/01 19:00",
        "01/01 20:00",
        "01/01 21:00",
        "01/01 22:00",
        "01/01 23:00",
        "01/02 00:00",
        "01/02 01:00",
        "01/02 02:00",
        "01/02 03:00",
        "01/02 04:00",
        "01/02 05:00",
        "01/02 06:00",
        "01/02 07:00",
        "01/02 08:00",
        "01/02 09:00",
        "01/02 10:00",
        "01/02 11:00",
        "01/02 12:00",
        "01/02 13:00",
        "01/02 14:00",
        "01/02 15:00",
        "01/02 16:00",
        "01/02 17:00",
        "01/02 18:00",
        "01/02 19:00",
        "01/02 20:00",
        "01/02 21:00",
        "01/02 22:00",
        "01/02 23:00",
        "01/03 00:00",
        "01/03 01:00",
        "01/03 02:00",
        "01/03 03:00",
        "01/03 04:00",
        "01/03 05:00",
        "01/03 06:00",
        "01/03 07:00",
        "01/03 08:00",
        "01/03 09:00",
        "01/03 10:00",
        "01/03 11:00",
        "01/03 12:00",
        "01/03 13:00",
        "01/03 14:00",
        "01/03 15:00",
        "01/03 16:00",
        "01/03 17:00",
        "01/03 18:00",
        "01/03 19:00",
        "01/03 20:00",
        "01/03 21:00",
        "01/03 22:00",
        "01/03 23:00",
        "01/04 00:00",
        "01/04 01:00",
        "01/04 02:00",
        "01/04 03:00",
        "01/04 04:00",
        "01/04 05:00",
        "01/04 06:00",
        "01/04 07:00",
        "01/04 08:00",
        "01/04 09:00",
        "01/04 10:00",
        "01/04 11:00",
        "01/04 12:00",
        "01/04 13:00",
        "01/04 14:00",
        "01/04 15:00",
        "01/04 16:00",
        "01/04 17:00",
        "01/04 18:00",
        "01/04 19:00",
        "01/04 20:00",
        "01/04 21:00",
        "01/04 22:00",
        "01/04 23:00",
        "01/05 00:00",
        "01/05 01:00",
        "01/05 02:00",
        "01/05 03:00",
        "01/05 04:00",
        "01/05 05:00",
        "01/05 06:00",
        "01/05 07:00",
        "01/05 08:00",
        "01/05 09:00",
        "01/05 10:00",
        "01/05 11:00",
        "01/05 12:00",
        "01/05 13:00",
        "01/05 14:00",
        "01/05 15:00",
        "01/05 16:00",
        "01/05 17:00",
        "01/05 18:00",
        "01/05 19:00",
        "01/05 20:00",
        "01/05 21:00",
        "01/05 22:00",
        "01/05 23:00",
        "01/06 00:00",
        "01/06 01:00",
        "01/06 02:00",
        "01/06 03:00",
        "01/06 04:00",
        "01/06 05:00",
        "01/06 06:00",
        "01/06 07:00",
        "01/06 08:00",
        "01/06 09:00",
        "01/06 10:00",
        "01/06 11:00",
        "01/06 12:00",
        "01/06 13:00",
        "01/06 14:00",
        "01/06 15:00",
        "01/06 16:00",
        "01/06 17:00",
        "01/06 18:00",
        "01/06 19:00",
        "01/06 20:00",
        "01/06 21:00",
        "01/06 22:00",
        "01/06 23:00",
        "01/07 00:00",
        "01/07 01:00",
        "01/07 02:00",
        "01/07 03:00",
        "01/07 04:00",
        "01/07 05:00",
        "01/07 06:00",
        "01/07 07:00",
        "01/07 08:00",
        "01/07 09:00",
        "01/07 10:00",
        "01/07 11:00",
        "01/07 12:00",
        "01/07 13:00",
        "01/07 14:00",
        "01/07 15:00",
        "01/07 16:00",
        "01/07 17:00",
        "01/07 18:00",
        "01/07 19:00",
        "01/07 20:00",
        "01/07 21:00",
        "01/07 22:00",
        "01/07 23:00",
    ],
}
