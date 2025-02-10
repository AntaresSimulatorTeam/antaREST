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

import { useState } from "react";
import { Box, TextField } from "@mui/material";
import LoadingButton from "@mui/lab/LoadingButton";
import { replaceMatrix } from "@/services/api/matrix";
import type { NonEmptyMatrix } from "../../shared/types";
import { useUpdateEffect } from "react-use";
import Transform from "@mui/icons-material/Transform";
import { resizeMatrix } from "../../shared/utils";

interface MatrixResizerProps {
  studyId: string;
  path: string;
  data: NonEmptyMatrix;
  onMatrixUpdated: VoidFunction;
}

function MatrixResizer({ studyId, path, data, onMatrixUpdated }: MatrixResizerProps) {
  // Use the first row's length as the initial column count.
  const initialColumnCount = data[0].length;
  const [columnCount, setColumnCount] = useState(initialColumnCount);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useUpdateEffect(() => {
    setColumnCount(initialColumnCount);
  }, [initialColumnCount]);

  const handleMatrixResize = async () => {
    if (columnCount === initialColumnCount) {
      return;
    }

    setIsSubmitting(true);

    try {
      const updatedMatrix = resizeMatrix({ matrix: data, newColumnCount: columnCount });
      await replaceMatrix(studyId, path, updatedMatrix);
      onMatrixUpdated();
    } catch (error) {
      console.error("Matrix resize failed:", error);
      // TODO add snackbar
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box sx={{ display: "flex", alignItems: "flex-end", gap: 1 }}>
      <TextField
        type="number"
        size="small"
        label="Columns"
        value={columnCount}
        onChange={(e) => setColumnCount(Number(e.target.value))}
        sx={{ m: 0, mt: 1, width: 100 }}
        slotProps={{
          htmlInput: {
            min: 1,
          },
        }}
      />
      <LoadingButton
        onClick={handleMatrixResize}
        loading={isSubmitting}
        loadingPosition="start"
        startIcon={<Transform />}
        variant="contained"
        size="small"
        disabled={columnCount === initialColumnCount}
      >
        Resize
      </LoadingButton>
    </Box>
  );
}

export default MatrixResizer;
