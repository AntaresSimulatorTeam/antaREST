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

import { useOutletContext } from "react-router";

import { StudyMetadata } from "@/common/types";
import Form from "@/components/common/Form";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getCurrentAreaId } from "@/redux/selectors";

import Fields from "./Fields";
import {
  getManagementOptionsFormFields,
  HydroFormFields,
  setManagementOptionsFormFields,
} from "./utils";

function ManagementOptions() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<HydroFormFields>) => {
    return setManagementOptionsFormFields(studyId, areaId, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={studyId + areaId}
      config={{
        defaultValues: () => getManagementOptionsFormFields(studyId, areaId),
      }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      <Fields />
    </Form>
  );
}

export default ManagementOptions;
