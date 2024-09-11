import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { AxiosError } from "axios";
import { Typography, Box, Divider } from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import {
  MatrixEditDTO,
  MatrixStats,
  StudyMetadata,
} from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { getStudyData, importFile } from "../../../services/api/study";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { editMatrix, getStudyMatrixIndex } from "../../../services/api/matrix";
import { Root, Content, Header } from "./style";
import SimpleLoader from "../loaders/SimpleLoader";
import EmptyView from "../page/SimpleContent";
import EditableMatrix from "../EditableMatrix";
import ImportDialog from "../dialogs/ImportDialog";
import MatrixAssignDialog from "./MatrixAssignDialog";
import { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import SplitButton from "../buttons/SplitButton";
import DownloadMatrixButton from "../DownloadMatrixButton.tsx";

interface Props {
  study: StudyMetadata;
  url: string;
  columnsNames?: string[] | readonly string[];
  rowNames?: string[];
  title?: string;
  computStats: MatrixStats;
  fetchFn?: fetchMatrixFn;
  disableEdit?: boolean;
  enablePercentDisplay?: boolean;
}

function MatrixInput({
  study,
  url,
  columnsNames,
  rowNames: initialRowNames,
  title,
  computStats,
  fetchFn,
  disableEdit,
  enablePercentDisplay,
}: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [openMatrixAsignDialog, setOpenMatrixAsignDialog] = useState(false);

  const {
    data: matrixData,
    isLoading,
    reload: reloadMatrix,
  } = usePromiseWithSnackbarError(fetchMatrixData, {
    errorMessage: t("data.error.matrix"),
    deps: [study.id, url, fetchFn],
  });

  const { data: matrixIndex } = usePromiseWithSnackbarError(
    async () => {
      if (fetchFn) {
        return matrixData?.index;
      }
      return getStudyMatrixIndex(study.id, url);
    },
    {
      errorMessage: t("matrix.error.failedToretrieveIndex"),
      deps: [study, url, fetchFn, matrixData],
    },
  );

  /**
   * If fetchFn is provided, custom row names (area names) are used from the matrixData's index property.
   * Otherwise, default row numbers and timestamps are displayed using initialRowNames.
   */
  const rowNames = fetchFn ? matrixIndex : initialRowNames;
  const columnsLength = matrixData?.columns?.length ?? 0;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  async function fetchMatrixData() {
    const res = fetchFn
      ? await fetchFn(study.id)
      : await getStudyData(study.id, url);
    if (typeof res === "string") {
      const fixed = res
        .replace(/NaN/g, '"NaN"')
        .replace(/Infinity/g, '"Infinity"');
      return JSON.parse(fixed);
    }
    return res;
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdate = async (change: MatrixEditDTO[], source: string) => {
    if (source !== "loadData" && source !== "updateData") {
      try {
        if (change.length > 0) {
          const sanitizedUrl = url.startsWith("/") ? url.substring(1) : url;
          await editMatrix(study.id, sanitizedUrl, change);
          enqueueSnackbar(t("matrix.success.matrixUpdate"), {
            variant: "success",
          });
        }
      } catch (e) {
        enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), e as AxiosError);
      }
    }
  };

  const handleImport = async (file: File) => {
    await importFile(file, study.id, url);
    reloadMatrix();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Content>
        <Header>
          <Typography
            sx={{
              color: "text.primary",
              fontSize: "1.25rem",
              fontWeight: 400,
              lineHeight: 1.334,
            }}
          >
            {title || t("xpansion.timeSeries")}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <SplitButton
              options={[
                t("global.import.fromFile"),
                t("global.import.fromDatabase"),
              ]}
              onClick={(_, index) => {
                if (index === 0) {
                  setOpenImportDialog(true);
                } else {
                  setOpenMatrixAsignDialog(true);
                }
              }}
              size="small"
              ButtonProps={{
                startIcon: <FileDownloadIcon />,
              }}
            >
              {t("global.import")}
            </SplitButton>
            <DownloadMatrixButton
              studyId={study.id}
              path={url}
              disabled={columnsLength === 0}
            />
          </Box>
        </Header>
        <Divider sx={{ width: "100%", mt: 1, mb: 2 }} />
        {isLoading && <SimpleLoader />}
        {!isLoading && columnsLength >= 1 && matrixIndex ? (
          <EditableMatrix
            matrix={matrixData}
            matrixTime={!rowNames}
            matrixIndex={matrixIndex}
            columnsNames={columnsNames}
            rowNames={rowNames}
            readOnly={!!disableEdit}
            onUpdate={handleUpdate}
            computStats={computStats}
            isPercentDisplayEnabled={enablePercentDisplay}
          />
        ) : (
          !isLoading && <EmptyView title={t("matrix.message.matrixEmpty")} />
        )}
      </Content>
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("matrix.importNewMatrix")}
          dropzoneText={t("matrix.message.importHint")}
          onCancel={() => setOpenImportDialog(false)}
          onImport={handleImport}
          accept={{ "text/*": [".csv", ".tsv", ".txt"] }}
        />
      )}
      {openMatrixAsignDialog && (
        <MatrixAssignDialog
          study={study}
          path={url}
          open={openMatrixAsignDialog}
          onClose={() => {
            setOpenMatrixAsignDialog(false);
            reloadMatrix();
          }}
        />
      )}
    </Root>
  );
}

export default MatrixInput;
