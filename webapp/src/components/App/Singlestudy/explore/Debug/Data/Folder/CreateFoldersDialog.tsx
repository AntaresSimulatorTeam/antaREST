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

import FormDialog from "@/components/common/dialogs/FormDialog.tsx";
import StringFE from "@/components/common/fieldEditors/StringFE.tsx";
import Fieldset from "@/components/common/Fieldset.tsx";
import { createFolder } from "@/services/api/studies/raw";
import type { StudyMetadata } from "@/common/types.ts";
import type { DataCompProps } from "@/components/App/Singlestudy/explore/Debug/utils.ts";
import type { SubmitHandlerPlus } from "@/components/common/Form/types.ts";

interface Props {
  open: boolean;
  onCancel: VoidFunction;
  studyId: StudyMetadata["id"];
  parentPath: string;
  reloadTreeData: DataCompProps["reloadTreeData"];
}

const defaultValues = { path: "" };

function CreateFoldersDialog({ open, onCancel, studyId, parentPath, reloadTreeData }: Props) {
  ////////////////////////////////////////////////////////////////",
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { path } }: SubmitHandlerPlus<typeof defaultValues>) => {
    return createFolder({ studyId, path: `${parentPath}/${path}` });
  };

  ////////////////////////////////////////////////////////////////",
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title="Create folder"
      config={{ defaultValues }}
      onCancel={onCancel}
      submitButtonText="Create"
      submitButtonIcon={null}
      cancelButtonText="Cancel"
      onSubmit={handleSubmit}
      onSubmitSuccessful={() => {
        reloadTreeData();
        onCancel();
      }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE label="Path" name="path" control={control} size="small" />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateFoldersDialog;
