/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../common/Form";
import { RENEWABLE_GROUPS, TS_INTERPRETATION_OPTIONS, type RenewableCluster } from "./utils";

function Fields() {
  const [t] = useTranslation();
  const { control } = useFormContextPlus<RenewableCluster>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset legend={t("global.general")}>
        <StringFE label={t("global.name")} name="name" control={control} disabled />
        <SelectFE
          label={t("global.group")}
          name="group"
          control={control}
          options={RENEWABLE_GROUPS}
          startCaseLabel={false}
          sx={{
            alignSelf: "center",
          }}
        />
        <SelectFE
          label={t("study.modelization.clusters.tsInterpretation")}
          name="tsInterpretation"
          control={control}
          options={TS_INTERPRETATION_OPTIONS}
          sx={{
            alignSelf: "center",
          }}
        />
      </Fieldset>
      <Fieldset legend={t("study.modelization.clusters.operatingParameters")}>
        <SwitchFE
          label={t("study.modelization.clusters.enabled")}
          name="enabled"
          control={control}
          sx={{
            alignItems: "center",
            alignSelf: "center",
          }}
        />
        <NumberFE
          label={t("study.modelization.clusters.unitcount")}
          name="unitCount"
          control={control}
          rules={{
            min: {
              value: 1,
              message: t("form.field.minValue", { 0: 1 }),
            },
            setValueAs: Math.floor,
          }}
        />
        <NumberFE
          label={t("study.modelization.clusters.nominalCapacity")}
          name="nominalCapacity"
          control={control}
          rules={{
            min: {
              value: 0,
              message: t("form.field.minValue", { 0: 0 }),
            },
          }}
        />
      </Fieldset>
    </>
  );
}

export default Fields;
