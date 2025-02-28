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
import { Box, Button, TextField } from "@mui/material";
import { useUpdateEffect } from "react-use";
import Transform from "@mui/icons-material/Transform";
import { resizeMatrix } from "../shared/utils";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import { useMatrixContext } from "../context/MatrixContext";

function MatrixResize() {
  const { data, currentState, setState, isSubmitting: isMatrixSubmitting } = useMatrixContext();

  const { t } = useTranslation();
  const errorSnackBar = useEnqueueErrorSnackbar();
  // Use the first row's length as the initial column count.
  const initialColumnCount = data[0].length;

  const [columnCount, setColumnCount] = useState(initialColumnCount);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useUpdateEffect(() => {
    setColumnCount(initialColumnCount);
  }, [initialColumnCount]);

  const handleMatrixResize = () => {
    if (columnCount === initialColumnCount) {
      return;
    }

    setIsSubmitting(true);

    try {
      const updatedMatrix = resizeMatrix({
        matrix: data,
        newColumnCount: columnCount,
      });

      setState({
        ...currentState,
        data: updatedMatrix,
        updateCount: currentState.updateCount + 1,
      });
    } catch (error) {
      errorSnackBar(t("matrix.error.matrixUpdate"), toError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <TextField
        type="number"
        size="small"
        value={columnCount}
        onChange={(e) => setColumnCount(Number(e.target.value))}
        disabled={isMatrixSubmitting}
        variant="outlined"
        sx={{
          width: 70,
          margin: 0,
        }}
        // TODO handle validation
        inputProps={{
          min: 1,
          max: 1000,
        }}
      />
      <Button
        onClick={handleMatrixResize}
        loading={isSubmitting}
        loadingPosition="start"
        startIcon={<Transform />}
        variant="contained"
        size="small"
        disabled={columnCount === initialColumnCount || isMatrixSubmitting}
      >
        {t("matrix.resize")}
      </Button>
    </Box>
  );
}

export default MatrixResize;
