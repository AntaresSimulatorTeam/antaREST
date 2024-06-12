/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { useOutletContext } from "react-router-dom";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import {
  createXpansionConfiguration,
  xpansionConfigurationExist,
} from "../../../../../services/api/xpansion";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import TabWrapper from "../TabWrapper";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../common/utils/UsePromiseCond";
import { Add } from "@mui/icons-material";

function Xpansion() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [exist, setExist] = useState<boolean>(false);

  const res = usePromiseWithSnackbarError(
    () => xpansionConfigurationExist(study.id),
    {
      errorMessage: t("xpansion.error.loadConfiguration"),
      deps: [exist],
    },
  );

  const tabList = useMemo(
    () => [
      {
        label: t("xpansion.candidates"),
        path: `/studies/${study?.id}/explore/xpansion/candidates`,
      },
      {
        label: t("global.settings"),
        path: `/studies/${study?.id}/explore/xpansion/settings`,
      },
      {
        label: t("xpansion.constraints"),
        path: `/studies/${study?.id}/explore/xpansion/constraints`,
      },
      {
        label: t("xpansion.weights"),
        path: `/studies/${study?.id}/explore/xpansion/weights`,
      },
      {
        label: t("xpansion.capacities"),
        path: `/studies/${study?.id}/explore/xpansion/capacities`,
      },
    ],
    [study],
  );

  useEffect(() => {
    if (window.history.state.usr) {
      setExist(window.history.state.usr.exist);
    } else {
      setExist(!!res.data);
    }
  }, [window.history.state.usr, res.data]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const createXpansion = async () => {
    try {
      if (study) {
        await createXpansionConfiguration(study.id);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("xpansion.error.createConfiguration"),
        e as AxiosError,
      );
    } finally {
      setExist(true);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      width="100%"
      flexGrow={1}
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
    >
      <UsePromiseCond
        response={res}
        ifResolved={(data) =>
          !data && !exist ? (
            <Button
              color="primary"
              variant="contained"
              size="small"
              startIcon={<Add />}
              onClick={createXpansion}
            >
              {t("xpansion.newXpansionConfig")}
            </Button>
          ) : (
            <TabWrapper
              study={study}
              tabStyle="withoutBorder"
              tabList={tabList}
            />
          )
        }
      />
    </Box>
  );
}

export default Xpansion;
