import { memo, useEffect, useMemo, useState } from "react";
import debug from "debug";
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
import { AxiosError } from "axios";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import AutoSizer from "react-virtualized-auto-sizer";
import HomeIcon from "@mui/icons-material/Home";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  areEqual,
  FixedSizeGrid,
  GridChildComponentProps,
  GridOnScrollProps,
} from "react-window";
import {
  GenericInfo,
  StudyMetadata,
  SortElement,
  SortItem,
  SortStatus,
} from "../../common/types";
import StudyCard from "./StudyCard";
import { STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from "../../theme";
import {
  deleteStudy,
  setStudyScrollPosition,
  StudiesState,
} from "../../redux/ducks/studies";
import {
  copyStudy as callCopyStudy,
  archiveStudy as callArchiveStudy,
  unarchiveStudy as callUnarchiveStudy,
} from "../../services/api/study";
import LauncherDialog from "./LauncherDialog";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import { useAppDispatch, useAppSelector } from "../../redux/hooks";
import useDebounce from "../../hooks/useDebounce";
import { getStudiesScrollPosition } from "../../redux/selectors";

const logError = debug("antares:studieslist:error");

const StudyCardCell = memo((props: GridChildComponentProps) => {
  const { data, columnIndex, rowIndex, style } = props;
  const {
    studies,
    importStudy,
    onLaunchClick,
    columnCount,
    columnWidth,
    favorites,
    onFavoriteClick,
    deleteStudy,
    archiveStudy,
    unarchiveStudy,
  } = data;
  const study = studies[columnIndex + rowIndex * columnCount];
  if (study) {
    return (
      <div style={{ display: "flex", justifyContent: "center", ...style }}>
        <StudyCard
          study={study}
          width={columnWidth}
          favorite={favorites.includes(study.id)}
          onLaunchClick={() => onLaunchClick(study)}
          onFavoriteClick={onFavoriteClick}
          onImportStudy={importStudy}
          onArchiveClick={archiveStudy}
          onUnarchiveClick={unarchiveStudy}
          onDeleteClick={deleteStudy}
        />
      </div>
    );
  }
  return <div />;
}, areEqual);

export interface StudiesListProps {
  studies: Array<StudyMetadata>;
  folder: string;
  setFolder: (folder: string) => void;
  favorites: StudiesState["favorites"];
  onFavoriteClick: (value: GenericInfo) => void;
  sortItem: SortItem;
  setSortItem: (value: SortItem) => void;
  refresh: VoidFunction;
}

function StudiesList(props: StudiesListProps) {
  const {
    studies,
    folder,
    sortItem,
    setFolder,
    favorites,
    setSortItem,
    onFavoriteClick,
    refresh,
  } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [folderList, setFolderList] = useState<Array<string>>([]);
  const [openLauncherDialog, setOpenLauncherDialog] = useState<boolean>(false);
  const [currentLaunchStudy, setCurrentLaunchStudy] = useState<StudyMetadata>();
  const scrollPosition = useAppSelector(getStudiesScrollPosition);
  const dispatch = useAppDispatch();

  const filterList = useMemo(
    () => [
      {
        element: SortElement.NAME,
        name: t("studies.sortByName"),
        status: SortStatus.INCREASE,
      },
      {
        element: SortElement.NAME,
        name: t("studies.sortByName"),
        status: SortStatus.DECREASE,
      },
      {
        element: SortElement.DATE,
        name: t("studies.sortByDate"),
        status: SortStatus.INCREASE,
      },
      {
        element: SortElement.DATE,
        name: t("studies.sortByDate"),
        status: SortStatus.DECREASE,
      },
    ],
    [t]
  );

  const importStudy = async (study: StudyMetadata, withOutputs: boolean) => {
    try {
      await callCopyStudy(
        study.id,
        `${study.name} (${t("study.copyId")})`,
        withOutputs
      );
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.copyStudy"), e as AxiosError);
      logError("Failed to copy/import study", study, e);
    }
  };

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.archive", { studyname: study.name }),
        e as AxiosError
      );
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.unarchive", { studyname: study.name }),
        e as AxiosError
      );
    }
  };

  const handleDeleteStudy = (study: StudyMetadata) => {
    dispatch(deleteStudy(study.id))
      .unwrap()
      .catch((err) => {
        enqueueErrorSnackbar(t("studies.error.deleteStudy"), err as AxiosError);
        logError("Failed to delete study", study, err);
      });
  };

  const getSortItem = (element: string): SortItem => {
    const tab = element.split("-");
    if (tab.length === 2) {
      return {
        element: tab[0] as SortElement,
        status: tab[1] as SortStatus,
      };
    }
    return {
      element: SortElement.NAME,
      status: SortStatus.INCREASE,
    };
  };

  const onLaunchClick = (study: StudyMetadata): void => {
    setCurrentLaunchStudy(study);
    setOpenLauncherDialog(true);
  };

  useEffect(() => {
    setFolderList(folder.split("/"));
  }, [folder]);

  const updateLastScroll = useDebounce(
    (scrollProp: GridOnScrollProps) => {
      dispatch(setStudyScrollPosition(scrollProp.scrollTop));
    },
    400,
    { trailing: true }
  );

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
            {folderList.map((elm, index) =>
              index === 0 ? (
                <HomeIcon
                  // eslint-disable-next-line react/no-array-index-key
                  key={`${elm}-${index}`}
                  sx={{
                    color: "text.primary",
                    cursor: "pointer",
                    "&:hover": {
                      color: "primary.main",
                    },
                  }}
                  onClick={() => setFolder("root")}
                />
              ) : (
                <Typography
                  // eslint-disable-next-line react/no-array-index-key
                  key={`${elm}-${index}`}
                  sx={{
                    color: "text.primary",
                    cursor: "pointer",
                    "&:hover": {
                      textDecoration: "underline",
                      color: "primary.main",
                    },
                  }}
                  onClick={() =>
                    setFolder(folderList.slice(0, index + 1).join("/"))
                  }
                >
                  {elm}
                </Typography>
              )
            )}
          </Breadcrumbs>
          <Typography mx={2} sx={{ color: "white" }}>
            ({`${studies.length} ${t("global.studies").toLowerCase()}`})
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
            <Button color="primary" onClick={refresh} variant="outlined">
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
            <InputLabel
              variant="standard"
              htmlFor={`single-checkbox-${t("studies.sortBy")}`}
            >
              {t("studies.sortBy")}
            </InputLabel>
            <Select
              labelId={`single-checkbox-label-${t("studies.sortBy")}`}
              id={`single-checkbox-${t("studies.sortBy")}`}
              value={`${sortItem.element}-${sortItem.status}`}
              label={t("studies.sortBy")}
              variant="filled"
              onChange={(e: SelectChangeEvent<string>) =>
                setSortItem(getSortItem(e.target.value as string))
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
              {filterList.map(({ element, name, status }) => {
                const value = `${element}-${status}`;
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
                      {status === SortStatus.INCREASE ? (
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
      <Box
        width="100%"
        height="100%"
        boxSizing="border-box"
        sx={{ overflowX: "hidden", overflowY: "auto" }}
      >
        <AutoSizer>
          {({ height, width }) => {
            const paddedWidth = width - 20;
            const columnWidth = paddedWidth / Math.round(paddedWidth / 400);
            const columnCount = Math.floor(paddedWidth / columnWidth);
            return (
              <FixedSizeGrid
                columnCount={columnCount}
                columnWidth={columnWidth}
                height={height}
                initialScrollTop={scrollPosition}
                onScroll={updateLastScroll}
                rowCount={Math.ceil(studies.length / columnCount)}
                rowHeight={260}
                width={width}
                itemData={{
                  studies,
                  importStudy,
                  onLaunchClick,
                  columnCount,
                  columnWidth,
                  favorites,
                  onFavoriteClick,
                  deleteStudy: handleDeleteStudy,
                  archiveStudy,
                  unarchiveStudy,
                }}
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </Box>
      {openLauncherDialog && (
        <LauncherDialog
          open={openLauncherDialog}
          study={currentLaunchStudy}
          onClose={() => setOpenLauncherDialog(false)}
        />
      )}
    </Box>
  );
}

export default StudiesList;
