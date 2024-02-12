import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import AddIcon from "@mui/icons-material/Add";
import {
  ChangeEvent,
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Button, Checkbox } from "@mui/material";
import { useTranslation } from "react-i18next";
import TableRowGroup from "./TableRowGroup";
import TableToolbar from "./TableToolbar";
import TableRowItem from "./TableRowItem";
import { Item, Column, AddItemDialogProps } from "./utils";

export interface DynamicDataTableProps {
  items: Item[];
  columns: Column[];
  onDeleteItems: (ids: string[]) => void;
  onAddItem: (item: Item) => void;
  AddItemDialog: FunctionComponent<AddItemDialogProps>;
}

function DynamicDataTable({
  items,
  columns,
  onDeleteItems,
  onAddItem,
  AddItemDialog,
}: DynamicDataTableProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const [openAddItemDialog, setOpenAddItemDialog] = useState(false);
  const { t } = useTranslation();

  const itemsByGroup = useMemo(() => {
    return items.reduce(
      (acc, item) => {
        if (item.group) {
          if (acc[item.group]) {
            acc[item.group].items.push(item);
          } else {
            acc[item.group] = { group: item.group, items: [item] };
          }
        }
        return acc;
      },
      {} as Record<string, { group: string; items: Item[] }>,
    );
  }, [items]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSelectAll = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      setSelected(e.target.checked ? items.map((item) => item.id) : []);
    },
    [items],
  );

  const handleSelect = useCallback(
    (_e: ChangeEvent<HTMLInputElement>, name: string) => {
      setSelected((prevSelected) => {
        if (prevSelected.includes(name)) {
          return prevSelected.filter((item) => item !== name);
        }
        return [...prevSelected, name];
      });
    },
    [],
  );

  const handleDelete = () => {
    onDeleteItems(selected);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const rows = useMemo(() => {
    const rowsArr = Object.values(itemsByGroup).map((items) => (
      <TableRowGroup
        key={items.group}
        itemsByGroup={items}
        columns={columns}
        selected={selected}
        onClick={handleSelect}
      />
    ));

    // Add items without group to rows
    items
      .filter((item) => !item.group)
      .forEach((item) =>
        rowsArr.push(
          <TableRowItem
            key={item.id}
            item={item}
            columns={columns}
            selected={selected}
            onClick={handleSelect}
          />,
        ),
      );

    return rowsArr;
  }, [items, itemsByGroup, columns, selected, handleSelect]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box sx={{ display: "flex", alignSelf: "flex-end" }}>
        <Button
          startIcon={<CompareArrowsIcon />}
          variant="outlined"
          size="small"
          sx={{ mt: 3, mr: 3 }}
          onClick={() => null}
        >
          {t("global.compare")}
        </Button>
        <Button
          startIcon={<AddIcon />}
          variant="outlined"
          size="small"
          sx={{ mt: 3, mr: 3 }}
          onClick={() => setOpenAddItemDialog(true)}
        >
          {t("button.add")}
        </Button>
      </Box>
      <TableContainer component={Box} sx={{ px: 3, mt: 1, pb: 3 }}>
        {selected.length > 0 && (
          <TableToolbar
            numSelected={selected.length}
            handleDelete={handleDelete}
          />
        )}
        <Table>
          <TableHead>
            <TableRow
              sx={{
                "& > *": {
                  backgroundColor: "rgba(34, 35, 51, 1)",
                  position: "sticky",
                  top: 0,
                  zIndex: 1,
                },
              }}
            >
              <TableCell sx={{ pl: 0 }}>
                <Checkbox
                  color="primary"
                  onChange={handleSelectAll}
                  checked={items.length > 0 && selected.length === items.length}
                />
              </TableCell>
              {columns.map((column) => (
                <TableCell
                  key={column.name}
                  align={column.operation ? "center" : "left"}
                >
                  {column.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
      {openAddItemDialog && (
        <AddItemDialog
          open={openAddItemDialog}
          onClose={() => setOpenAddItemDialog(false)}
          onAddItem={onAddItem}
        />
      )}
    </>
  );
}

export default DynamicDataTable;
