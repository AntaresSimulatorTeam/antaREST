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

import "@glideapps/glide-data-grid/dist/index.css";
import DataEditor, {
  CompactSelection,
  EditableGridCell,
  EditListItem,
  GridCellKind,
  GridColumn,
  GridSelection,
  Item,
} from "@glideapps/glide-data-grid";
import { useGridCellContent } from "./useGridCellContent";
import { useMemo, useState } from "react";
import { EnhancedGridColumn, GridUpdate, MatrixAggregates } from "./types";
import { darkTheme, readOnlyDarkTheme } from "./utils";
import { useColumnMapping } from "./useColumnMapping";

export interface MatrixGridProps {
  data: number[][];
  rows: number;
  columns: EnhancedGridColumn[];
  dateTime?: string[];
  aggregates?: MatrixAggregates;
  rowHeaders?: string[];
  width?: string;
  height?: string;
  onCellEdit?: (update: GridUpdate) => void;
  onMultipleCellsEdit?: (updates: GridUpdate[]) => void;
  isReaOnlyEnabled?: boolean;
  isPercentDisplayEnabled?: boolean;
}

function MatrixGrid({
  data,
  rows,
  columns: initialColumns,
  dateTime,
  aggregates,
  rowHeaders,
  width = "100%",
  height = "100%",
  onCellEdit,
  onMultipleCellsEdit,
  isReaOnlyEnabled,
  isPercentDisplayEnabled,
}: MatrixGridProps) {
  const [columns, setColumns] = useState<EnhancedGridColumn[]>(initialColumns);
  const [selection, setSelection] = useState<GridSelection>({
    columns: CompactSelection.empty(),
    rows: CompactSelection.empty(),
  });

  const { gridToData } = useColumnMapping(columns);

  const theme = useMemo(() => {
    if (isReaOnlyEnabled) {
      return {
        ...darkTheme,
        ...readOnlyDarkTheme,
      };
    }

    return darkTheme;
  }, [isReaOnlyEnabled]);

  const getCellContent = useGridCellContent(
    data,
    columns,
    gridToData,
    dateTime,
    aggregates,
    rowHeaders,
    isReaOnlyEnabled,
    isPercentDisplayEnabled,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////
  const handleColumnResize = (
    column: GridColumn,
    newSize: number,
    colIndex: number,
    newSizeWithGrow: number,
  ) => {
    const newColumns = columns.map((col, index) =>
      index === colIndex ? { ...col, width: newSize } : col,
    );

    setColumns(newColumns);
  };

  const handleCellEdited = (coordinates: Item, value: EditableGridCell) => {
    if (value.kind !== GridCellKind.Number) {
      // Invalid numeric value
      return;
    }

    const dataCoordinates = gridToData(coordinates);

    if (dataCoordinates && onCellEdit) {
      onCellEdit({ coordinates: dataCoordinates, value });
    }
  };

  const handleCellsEdited = (newValues: readonly EditListItem[]) => {
    const updates = newValues
      .map((edit): GridUpdate | null => {
        const dataCoordinates = gridToData(edit.location);

        if (edit.value.kind !== GridCellKind.Number || !dataCoordinates) {
          return null;
        }

        return {
          coordinates: dataCoordinates,
          value: edit.value,
        };
      })
      .filter((update): update is GridUpdate => update !== null);

    if (updates.length === 0) {
      // No valid updates
      return;
    }

    if (onCellEdit && updates.length === 1) {
      // If only one cell is edited,`onCellEdit` is called
      // we don't need to call `onMultipleCellsEdit`
      return;
    }

    if (onMultipleCellsEdit) {
      onMultipleCellsEdit(updates);
    }

    // Return true to prevent calling `onCellEdit`
    // for each cell after`onMultipleCellsEdit` is called
    return true;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <DataEditor
        theme={theme}
        width={width}
        height={height}
        rows={rows}
        columns={columns}
        getCellContent={getCellContent}
        onCellEdited={handleCellEdited}
        onCellsEdited={handleCellsEdited}
        gridSelection={selection}
        onGridSelectionChange={setSelection}
        getCellsForSelection // Enable copy support
        onPaste
        fillHandle
        rowMarkers="both"
        freezeColumns={1} // Make the first column sticky
        onColumnResize={handleColumnResize}
      />
      <div id="portal" />
    </>
  );
}

export default MatrixGrid;
