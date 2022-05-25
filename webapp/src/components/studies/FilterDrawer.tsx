import { useTranslation } from "react-i18next";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Divider from "@mui/material/Divider";
import {
  Button,
  Checkbox,
  Drawer,
  FormControlLabel,
  List,
  ListItem,
  Typography,
} from "@mui/material";
import { useRef } from "react";
import { STUDIES_FILTER_WIDTH } from "../../theme";
import useAppSelector from "../../redux/hooks/useAppSelector";
import {
  getGroups,
  getStudyFilters,
  getStudyVersions,
  getUsers,
} from "../../redux/selectors";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../redux/ducks/studies";
import CheckboxesTags from "../common/inputs/CheckboxesTags";
import { displayVersionName } from "../../services/utils";

interface Props {
  open: boolean;
  onClose: () => void;
}

function FilterDrawer(props: Props) {
  const { open, onClose } = props;
  const [t] = useTranslation();
  const filters = useAppSelector(getStudyFilters);
  const versions = useAppSelector(getStudyVersions);
  const users = useAppSelector(getUsers);
  const groups = useAppSelector(getGroups);
  const dispatch = useAppDispatch();
  const managedValueRef = useRef(filters.managed);
  const archivedValueRef = useRef(filters.archived);
  const versionsSelectedRef = useRef(filters.versions);
  const usersSelectedRef = useRef(filters.users);
  const groupsSelectedRef = useRef(filters.groups);
  const tagsSelectedRef = useRef(filters.tags);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFilter = () => {
    dispatch(
      updateStudyFilters({
        managed: managedValueRef.current,
        archived: archivedValueRef.current,
        versions: versionsSelectedRef.current,
        users: usersSelectedRef.current,
        groups: groupsSelectedRef.current,
        tags: tagsSelectedRef.current,
      })
    );

    onClose();
  };

  const handleReset = () => {
    dispatch(
      updateStudyFilters({
        managed: false,
        archived: false,
        versions: [],
        users: [],
        groups: [],
        tags: [],
      })
    );

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Drawer
      variant="temporary"
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: STUDIES_FILTER_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: STUDIES_FILTER_WIDTH,
          boxSizing: "border-box",
          overflow: "hidden",
        },
      }}
    >
      <Toolbar sx={{ py: 3 }}>
        <Box
          display="flex"
          width="100%"
          height="100%"
          justifyContent="flex-start"
          alignItems="flex-start"
          py={2}
          flexDirection="column"
          flexWrap="nowrap"
          boxSizing="border-box"
          color="white"
        >
          <Typography sx={{ color: "grey.500", fontSize: "0.9em", mb: 2 }}>
            {t("global.filter").toUpperCase()}
          </Typography>
          <FormControlLabel
            control={
              <Checkbox
                sx={{ color: "white" }}
                name="managed"
                defaultChecked={filters.managed}
                onChange={(_, checked) => {
                  managedValueRef.current = checked;
                }}
              />
            }
            label={t("studies.managedStudiesFilter") as string}
          />
          <FormControlLabel
            control={
              <Checkbox
                sx={{ color: "white" }}
                name="archived"
                defaultChecked={filters.archived}
                onChange={(_, checked) => {
                  archivedValueRef.current = checked;
                }}
              />
            }
            label={t("studies.archivedStudiesFilter") as string}
          />
        </Box>
      </Toolbar>
      <Divider style={{ height: "1px", backgroundColor: "grey.800" }} />
      <List>
        <ListItem>
          <CheckboxesTags
            label={t("global.versions")}
            options={versions}
            getOptionLabel={displayVersionName}
            defaultValue={filters.versions}
            onChange={(_, value) => {
              versionsSelectedRef.current = value;
            }}
          />
        </ListItem>
        <ListItem>
          <CheckboxesTags
            label={t("global.users")}
            options={users}
            getOptionLabel={(option) => option.name}
            defaultValue={users.filter((user) =>
              filters.users.includes(user.id)
            )}
            onChange={(event, value) => {
              usersSelectedRef.current = value.map((val) => val.id);
            }}
          />
        </ListItem>
        <ListItem>
          <CheckboxesTags
            label={t("global.groups")}
            options={groups}
            getOptionLabel={(option) => option.name}
            defaultValue={groups.filter((group) =>
              filters.groups.includes(group.id)
            )}
            onChange={(_, value) => {
              groupsSelectedRef.current = value.map((val) => val.id);
            }}
          />
        </ListItem>
        <ListItem>
          <CheckboxesTags
            label={t("global.tags")}
            options={[]}
            defaultValue={filters.tags}
            onChange={(_, value) => {
              tagsSelectedRef.current = value;
            }}
            freeSolo
          />
        </ListItem>
      </List>
      <Box
        display="flex"
        width="100%"
        flexGrow={1}
        justifyContent="flex-end"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <Box
          display="flex"
          width="100%"
          height="auto"
          justifyContent="flex-end"
          alignItems="center"
          flexDirection="row"
          flexWrap="nowrap"
          boxSizing="border-box"
          p={1}
        >
          <Button variant="outlined" onClick={handleReset}>
            {t("global.reset")}
          </Button>
          <Button sx={{ mx: 2 }} variant="contained" onClick={handleFilter}>
            {t("global.filter")}
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
}

export default FilterDrawer;
