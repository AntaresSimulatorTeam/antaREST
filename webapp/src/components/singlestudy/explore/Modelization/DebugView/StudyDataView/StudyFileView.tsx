/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useState } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { getStudyData, importFile } from "../../../../../../services/api/study";
import { Header, Root, Content } from "./style";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import ImportForm from "../../../../../common/ImportForm";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";

const logErr = debug("antares:createimportform:error");

interface PropTypes {
  study: string;
  url: string;
  refreshView: () => void;
  filterOut: Array<string>;
}

function StudyDataView(props: PropTypes) {
  const { study, url, filterOut, refreshView } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const [isEditable, setEditable] = useState<boolean>(true);
  const [formatedPath, setFormatedPath] = useState<string>("");

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      if (typeof res === "object") {
        setData(res.join("\n"));
      } else {
        setData(res);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.retrieveData"), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  const onImport = async (file: File) => {
    try {
      await importFile(file, study, formatedPath);
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
    }
    refreshView();
    enqueueSnackbar(t("studies.success.saveData"), {
      variant: "success",
    });
  };

  useEffect(() => {
    const urlParts = url.split("/");
    const tmpUrl = urlParts.filter((item) => item);
    setFormatedPath(tmpUrl.join("/"));
    if (tmpUrl.length > 0) {
      setEditable(!filterOut.includes(tmpUrl[0]));
    }
    if (urlParts.length < 2) {
      enqueueSnackbar(t("studies.error.retrieveData"), {
        variant: "error",
      });
      return;
    }
    loadFileData();
  }, [url, filterOut]);

  return (
    <>
      {data && (
        <Root>
          {isEditable && (
            <Header>
              <ImportForm text={t("global.import")} onImport={onImport} />
            </Header>
          )}
          <Content>
            <code style={{ whiteSpace: "pre" }}>{data}</code>
          </Content>
        </Root>
      )}
      {!loaded && (
        <Box width="100%" height="100%" position="relative">
          <SimpleLoader />
        </Box>
      )}
    </>
  );
}

export default StudyDataView;
