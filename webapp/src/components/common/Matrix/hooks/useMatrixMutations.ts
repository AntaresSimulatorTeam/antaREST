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

import { useState, useCallback } from "react";
import { t } from "i18next";
import { updateMatrix } from "@/services/api/matrix";
import { uploadFile } from "@/services/api/studies/raw";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import type { GridUpdate, AggregateType } from "../shared/types";
import { calculateMatrixAggregates } from "../shared/utils";
import type { Actions } from "use-undo";
import { toError } from "@/utils/fnUtils";
import type { DataState } from "./useMatrixData";

interface UseMatrixMutationsProps {
  studyId: string;
  path: string;
  currentState: DataState;
  setState: Actions<DataState>["set"];
  reload: VoidFunction; // check type
  aggregateTypes: AggregateType[];
}

export function useMatrixMutations({
  studyId,
  path,
  currentState,
  setState,
  reload,
  aggregateTypes,
}: UseMatrixMutationsProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const applyUpdates = useCallback(
    (updates: GridUpdate[]) => {
      const updatedData = currentState.data.map((col) => [...col]);

      for (const {
        coordinates: [row, col],
        value,
      } of updates) {
        if (value.kind === "number" && value.data !== undefined) {
          updatedData[col][row] = value.data;
        }
      }

      const newAggregates = calculateMatrixAggregates({
        matrix: updatedData,
        types: aggregateTypes,
      });

      setState({
        data: updatedData,
        aggregates: newAggregates,
        updateCount: currentState.updateCount + 1 || 1,
      });
    },
    [currentState, setState, aggregateTypes],
  );

  const handleCellEdit = useCallback(
    (update: GridUpdate) => {
      applyUpdates([update]);
    },
    [applyUpdates],
  );

  const handleMultipleCellsEdit = useCallback(
    (updates: GridUpdate[]) => {
      applyUpdates(updates);
    },
    [applyUpdates],
  );

  const handleUpload = useCallback(
    async (file: File) => {
      try {
        await uploadFile({ file, studyId, path: path });

        reload();
      } catch (error) {
        enqueueErrorSnackbar(t("matrix.error.import"), toError(error));
      }
    },
    [studyId, path, reload, enqueueErrorSnackbar],
  );

  const handleSaveUpdates = useCallback(async () => {
    if (currentState.updateCount <= 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      const updatedMatrix = await updateMatrix(studyId, path, currentState.data);

      setState({
        ...currentState,
        data: updatedMatrix,
        updateCount: 0,
      });
    } catch (error) {
      enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), toError(error));
    } finally {
      setIsSubmitting(false);
    }
  }, [currentState, studyId, path, setState, enqueueErrorSnackbar]);

  return {
    isSubmitting,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleUpload,
    handleSaveUpdates,
  };
}
