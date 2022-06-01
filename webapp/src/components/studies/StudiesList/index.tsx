import { useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Typography,
  Breadcrumbs,
  Select,
  MenuItem,
  ListItemText,
  SelectChangeEvent,
  ListItemIcon,
  Button,
  Tooltip,
  FormControl,
  InputLabel,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import AutoSizer from "react-virtualized-auto-sizer";
import HomeIcon from "@mui/icons-material/Home";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import RefreshIcon from "@mui/icons-material/Refresh";
import { FixedSizeGrid, GridOnScrollProps } from "react-window";
import { v4 as uuidv4 } from "uuid";
import { StudyMetadata } from "../../../common/types";
import {
  STUDIES_HEIGHT_HEADER,
  STUDIES_LIST_HEADER_HEIGHT,
} from "../../../theme";
import {
  fetchStudies,
  setStudyScrollPosition,
  StudiesSortConf,
  updateStudiesSortConf,
  updateStudyFilters,
} from "../../../redux/ducks/studies";
import LauncherDialog from "../LauncherDialog";
import useDebounce from "../../../hooks/useDebounce";
import {
  getStudiesScrollPosition,
  getStudiesSortConf,
  getStudyFilters,
} from "../../../redux/selectors";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import StudyCardCell from "./StudyCardCell";

const CARD_TARGET_WIDTH = 500;
const CARD_HEIGHT = 250;

export interface StudiesListProps {
  studyIds: Array<StudyMetadata["id"]>;
}

function StudiesList(props: StudiesListProps) {
  const { studyIds } = props;
  const [t] = useTranslation();
  const [studyToLaunch, setStudyToLaunch] = useState<
    StudyMetadata["id"] | null
  >(null);
  const scrollPosition = useAppSelector(getStudiesScrollPosition);
  const sortConf = useAppSelector(getStudiesSortConf);
  const folder = useAppSelector((state) => getStudyFilters(state).folder);
  const [folderList, setFolderList] = useState(folder.split("/"));
  const dispatch = useAppDispatch();
  const sortLabelId = useRef(uuidv4()).current;

  useEffect(() => {
    setFolderList(folder.split("/"));
  }, [folder]);

  const sortOptions = useMemo<Array<StudiesSortConf & { name: string }>>(
    () => [
      {
        name: t("studies.sortByName"),
        property: "name",
        order: "ascend",
      },
      {
        name: t("studies.sortByName"),
        property: "name",
        order: "descend",
      },
      {
        name: t("studies.sortByDate"),
        property: "modificationDate",
        order: "ascend",
      },
      {
        name: t("studies.sortByDate"),
        property: "modificationDate",
        order: "descend",
      },
    ],
    [t]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleScroll = useDebounce(
    (scrollProp: GridOnScrollProps) => {
      dispatch(setStudyScrollPosition(scrollProp.scrollTop));
    },
    400,
    { trailing: true }
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setFolder = (value: string) => {
    dispatch(updateStudyFilters({ folder: value }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      height={`calc(100vh - ${STUDIES_HEIGHT_HEADER}px)`}
      flex={1}
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      sx={{ overflowX: "hidden", overflowY: "hidden" }}
    >
      <Box
        width="100%"
        height={`${STUDIES_LIST_HEADER_HEIGHT}px`}
        px={2}
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
        boxSizing="border-box"
      >
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <Breadcrumbs
            separator={<NavigateNextIcon fontSize="small" />}
            aria-label="breadcrumb"
          >
            {folderList.map((fol, index) => {
              const path = folderList.slice(0, index + 1).join("/");
              if (index === 0) {
                return (
                  <HomeIcon
                    key={path}
                    sx={{
                      color: "text.primary",
                      cursor: "pointer",
                      "&:hover": {
                        color: "primary.main",
                      },
                    }}
                    onClick={() => setFolder("root")}
                  />
                );
              }
              return (
                <Typography
                  key={path}
                  sx={{
                    color: "text.primary",
                    cursor: "pointer",
                    "&:hover": {
                      textDecoration: "underline",
                      color: "primary.main",
                    },
                  }}
                  onClick={() => setFolder(path)}
                >
                  {fol}
                </Typography>
              );
            })}
          </Breadcrumbs>
          <Typography mx={2} sx={{ color: "white" }}>
            ({`${studyIds.length} ${t("global.studies").toLowerCase()}`})
          </Typography>
        </Box>
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="center"
          alignItems="center"
          boxSizing="border-box"
        >
          <Tooltip title={t("studies.refresh") as string} sx={{ mr: 4 }}>
            <Button
              color="primary"
              onClick={() => dispatch(fetchStudies())}
              variant="outlined"
            >
              <RefreshIcon />
            </Button>
          </Tooltip>
          <FormControl
            sx={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "flex-start",
              boxSizing: "border-box",
            }}
          >
            <InputLabel id={sortLabelId} variant="standard">
              {t("studies.sortBy")}
            </InputLabel>
            <Select
              labelId={sortLabelId}
              value={JSON.stringify(sortConf)}
              label={t("studies.sortBy")}
              variant="filled"
              onChange={(e: SelectChangeEvent<string>) =>
                dispatch(updateStudiesSortConf(JSON.parse(e.target.value)))
              }
              sx={{
                width: "230px",
                height: "45px",
                ".MuiSelect-select": {
                  display: "flex",
                  flexFlow: "row nowrap",
                  justifyContent: "center",
                  alignItems: "center",
                },
                background: "rgba(255, 255, 255, 0)",
                borderRadius: "4px 4px 0px 0px",
                borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
                ".MuiSelect-icon": {
                  backgroundColor: "#222333",
                },
              }}
            >
              {sortOptions.map(({ name, ...conf }) => {
                const value = JSON.stringify(conf);
                return (
                  <MenuItem
                    key={value}
                    value={value}
                    sx={{
                      display: "flex",
                      flexFlow: "row nowrap",
                      justifyContent: "center",
                      alignItems: "center",
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: "30px" }}>
                      {conf.order === "ascend" ? (
                        <ArrowUpwardIcon />
                      ) : (
                        <ArrowDownwardIcon />
                      )}
                    </ListItemIcon>
                    <ListItemText primary={name} />
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
        </Box>
      </Box>
      <Box sx={{ width: 1, height: 1 }}>
        <AutoSizer>
          {({ height, width }) => {
            const paddedWidth = width - 10;
            const columnWidth =
              paddedWidth / Math.floor(paddedWidth / CARD_TARGET_WIDTH);
            const columnCount = Math.floor(paddedWidth / columnWidth);
            const rowHeight = CARD_HEIGHT;
            return (
              <FixedSizeGrid
                key={JSON.stringify(studyIds)}
                columnCount={columnCount}
                columnWidth={columnWidth}
                height={height}
                width={width}
                rowCount={Math.ceil(studyIds.length / columnCount)}
                rowHeight={rowHeight}
                initialScrollTop={scrollPosition}
                onScroll={handleScroll}
                useIsScrolling
                itemData={{
                  studyIds,
                  setStudyToLaunch,
                  columnCount,
                  columnWidth,
                  rowHeight,
                }}
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </Box>
      {studyToLaunch && (
        <LauncherDialog
          open
          studyId={studyToLaunch}
          onClose={() => setStudyToLaunch(null)}
        />
      )}
    </Box>
  );
}

export default StudiesList;
