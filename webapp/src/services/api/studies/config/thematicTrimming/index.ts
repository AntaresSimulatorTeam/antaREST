/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type {
  GetThematicTrimmingConfigParams,
  SetThematicTrimmingConfigParams,
  ThematicTrimmingConfig,
} from "./types";
import client from "../../../client";
import { format } from "../../../../../utils/stringUtils";

const URL = "/v1/studies/{studyId}/config/thematictrimming/form";

export async function getThematicTrimmingConfig({ studyId }: GetThematicTrimmingConfigParams) {
  const url = format(URL, { studyId });
  const { data } = await client.get<ThematicTrimmingConfig>(url);
  return data;
}

export async function setThematicTrimmingConfig({
  studyId,
  config,
}: SetThematicTrimmingConfigParams) {
  const url = format(URL, { studyId });
  await client.put(url, config);
}
