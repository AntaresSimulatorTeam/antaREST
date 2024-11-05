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

import { useMemo } from "react";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";

import AddCircleIcon from "@mui/icons-material/AddCircle";

import { StudyMetadata } from "@/common/types";
import FormDialog from "@/components/common/dialogs/FormDialog";
import StringFE from "@/components/common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { createStudyMapLayer } from "@/redux/ducks/studyMaps";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyMapLayersById } from "@/redux/selectors";
import { validateString } from "@/utils/validation/string";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  name: "",
};

function CreateLayerDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const layersById = useAppSelector(getStudyMapLayersById);

  const existingLayers = useMemo(
    () => Object.values(layersById).map(({ name }) => name),
    [layersById],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    try {
      dispatch(
        createStudyMapLayer({ studyId: study.id, name: data.values.name }),
      );
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createLayer"), e as AxiosError);
    }

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modelization.map.layers.add")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control }) => (
        <StringFE
          label={t("global.name")}
          name="name"
          control={control}
          fullWidth
          rules={{
            validate: (v) =>
              validateString(v, { existingValues: existingLayers }),
          }}
        />
      )}
    </FormDialog>
  );
}

export default CreateLayerDialog;
