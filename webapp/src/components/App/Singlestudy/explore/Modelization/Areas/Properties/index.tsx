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

import { Paper } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import Form from "../../../../../../common/Form";
import {
  PropertiesFormFields,
  getPropertiesFormFields,
  setPropertiesFormFields,
} from "./utils";
import Fields from "./Fields";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";

function Properties() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentAreaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<PropertiesFormFields>) => {
    const { dirtyValues } = data;
    return setPropertiesFormFields(study.id, currentAreaId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper sx={{ width: 1, height: 1, padding: 2, overflow: "auto" }}>
      <Form
        key={study.id + currentAreaId}
        config={{
          defaultValues: () => getPropertiesFormFields(study.id, currentAreaId),
        }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        <Fields />
      </Form>
    </Paper>
  );
}

export default Properties;
