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

import { Box, Divider, Skeleton } from "@mui/material";
import MatrixGrid from "./components/MatrixGrid";
import { useMatrix } from "./hooks/useMatrix";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../common/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";
import MatrixActions from "./components/MatrixActions";
import EmptyView from "../page/EmptyView";
import type { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import { isNonEmptyMatrix, type AggregateConfig } from "./shared/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import MatrixUpload from "@/components/common/Matrix/components/MatrixUpload";
import MatrixResizer from "./components/MatrixResizer";

interface MatrixProps {
  url: string;
  title?: string;
  customRowHeaders?: string[];
  dateTimeColumn?: boolean;
  isTimeSeries?: boolean;
  aggregateColumns?: AggregateConfig;
  rowHeaders?: boolean;
  showPercent?: boolean;
  readOnly?: boolean;
  customColumns?: string[] | readonly string[];
  colWidth?: number;
  fetchMatrixData?: fetchMatrixFn;
  canImport?: boolean;
}

function Matrix({
  url,
  title = "global.timeSeries",
  customRowHeaders = [],
  dateTimeColumn = true,
  isTimeSeries = true,
  aggregateColumns = false,
  rowHeaders = customRowHeaders.length > 0,
  showPercent = false,
  readOnly = false,
  customColumns,
  colWidth,
  fetchMatrixData,
  canImport = false,
}: MatrixProps) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [uploadType, setUploadType] = useState<"file" | "database" | undefined>(undefined);

  // TODO: split `useMatrix` into smaller units
  const {
    data,
    aggregates,
    error,
    isLoading,
    isSubmitting,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleUpload,
    handleSaveUpdates,
    pendingUpdatesCount,
    undo,
    redo,
    canUndo,
    canRedo,
    reload,
    rowCount,
  } = useMatrix(
    study.id,
    url,
    dateTimeColumn,
    isTimeSeries,
    rowHeaders,
    aggregateColumns,
    customColumns,
    colWidth,
    fetchMatrixData,
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isLoading) {
    return <Skeleton sx={{ height: 1, transform: "none" }} />;
  }

  if (error) {
    return <EmptyView title={error.message} />;
  }

  return (
    <MatrixContainer>
      <MatrixHeader>
        <MatrixTitle>{t(title)}</MatrixTitle>
        <Box sx={{ display: "flex", gap: 1 }}>
          {isNonEmptyMatrix(data) && isTimeSeries && (
            <MatrixResizer studyId={study.id} path={url} data={data} onMatrixUpdated={reload} />
          )}
          <MatrixActions
            onImport={(_, index) => {
              setUploadType(index === 0 ? "file" : "database");
            }}
            onSave={handleSaveUpdates}
            studyId={study.id}
            path={url}
            disabled={data.length === 0}
            pendingUpdatesCount={pendingUpdatesCount}
            isSubmitting={isSubmitting}
            undo={undo}
            redo={redo}
            canUndo={canUndo}
            canRedo={canRedo}
            canImport={canImport}
          />
        </Box>
      </MatrixHeader>
      <Divider sx={{ width: 1, mt: 1, mb: 2 }} />
      {isNonEmptyMatrix(data) ? (
        <MatrixGrid
          data={data}
          aggregates={aggregates}
          columns={columns}
          rows={rowCount ?? data.length}
          rowHeaders={customRowHeaders}
          dateTime={dateTime}
          onCellEdit={handleCellEdit}
          onMultipleCellsEdit={handleMultipleCellsEdit}
          readOnly={isSubmitting || readOnly}
          showPercent={showPercent}
        />
      ) : (
        <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOffIcon} />
      )}
      {uploadType === "file" && (
        <MatrixUpload
          studyId={study.id}
          path={url}
          type="file"
          open={true}
          onClose={() => setUploadType(undefined)}
          onFileUpload={handleUpload}
          fileOptions={{
            accept: { "text/*": [".csv", ".tsv", ".txt"] },
            dropzoneText: t("matrix.message.importHint"),
          }}
        />
      )}
      {uploadType === "database" && (
        <MatrixUpload
          studyId={study.id}
          path={url}
          type="database"
          open={true}
          onClose={() => {
            setUploadType(undefined);
            reload();
          }}
        />
      )}
    </MatrixContainer>
  );
}

export default Matrix;
