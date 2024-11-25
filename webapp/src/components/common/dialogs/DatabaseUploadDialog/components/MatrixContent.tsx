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
import { useTranslation } from "react-i18next";
import { Box, Divider, Typography } from "@mui/material";
import { MatrixInfoDTO, MatrixDTO } from "@/common/types";
import MatrixGrid from "@/components/common/Matrix/components/MatrixGrid";
import ButtonBack from "@/components/common/ButtonBack";
import { getMatrix } from "@/services/api/matrix";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { generateDataColumns } from "@/components/common/Matrix/shared/utils";
import EmptyView from "@/components/common/page/SimpleContent";
import { GridOff } from "@mui/icons-material";

interface MatrixContentProps {
  matrix: MatrixInfoDTO;
  onBack: () => void;
}

function MatrixContent({ matrix, onBack }: MatrixContentProps) {
  const { t } = useTranslation();

  const { data: matrixData } = usePromiseWithSnackbarError<MatrixDTO>(
    () => getMatrix(matrix.id),
    {
      errorMessage: t("data.error.matrix"),
    },
  );

  const matrixColumns = useMemo(
    () =>
      matrixData ? generateDataColumns(true, matrixData.columns.length) : [],
    [matrixData],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!matrixData) {
    return null;
  }

  return (
    <>
      <Box sx={{ display: "flex" }}>
        <ButtonBack onClick={onBack} />
        <Typography>{matrix.name}</Typography>
      </Box>
      <Divider sx={{ mt: 1, mb: 2 }} />
      {!matrixData.data[0]?.length ? (
        <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOff} />
      ) : (
        <MatrixGrid
          data={matrixData.data}
          columns={matrixColumns}
          rows={matrixData.data.length}
          readOnly
        />
      )}
    </>
  );
}

export default MatrixContent;
