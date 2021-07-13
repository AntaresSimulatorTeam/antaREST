import React, { createRef, useEffect, useRef, useState } from 'react';
import { HotTable, HotColumn } from '@handsontable/react';
import { createStyles, makeStyles } from '@material-ui/core';
import DataTable from 'frappe-datatable';
import { MatrixType } from '../../../../common/types';
import 'handsontable/dist/handsontable.min.css';
import 'frappe-datatable/dist/frappe-datatable.css';

const useStyles = makeStyles(() =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      overflow: 'auto',
    },
  }));

interface PropTypes {
  matrix: MatrixType;
  readOnly: boolean;
}

type CellType = Array<number | string | boolean>;
type ColumnsType = { title: string; readOnly: boolean };

export default function MatrixView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { readOnly, matrix } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const classes = useStyles();
  const prependIndex = index.length > 0 && typeof index[0] === 'string';
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setColumns] = useState<Array<ColumnsType>>([]);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      console.log(grid)
      // eslint-disable-next-line no-new
      new DataTable('#datatable', {
        columns: formatedColumns.map((col) => col.title),
        data: grid,
      });
    }
  }, [formatedColumns, grid, ref]);

  useEffect(() => {
    const columnsData: Array<ColumnsType> = (
      prependIndex ? [{ title: 'Time', readOnly }] : []
    ).concat(columns.map((title) => ({ title: String(title), readOnly })));
    setColumns(columnsData);

    const tmpData = data.map((row, i) => (prependIndex ? [index[i]].concat(row) : row));
    setGrid(tmpData);
  }, [columns, data, index, prependIndex, readOnly]);

  return <div id="datatable" ref={ref} />;
}
