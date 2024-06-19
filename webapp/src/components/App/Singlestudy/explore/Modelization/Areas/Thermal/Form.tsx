import { useCallback } from "react";
import { Box, Button } from "@mui/material";
import { useParams, useOutletContext, useNavigate } from "react-router-dom";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import Form from "../../../../../../common/Form";
import Fields from "./Fields";
import Matrix from "./Matrix";
import {
  ThermalCluster,
  getThermalCluster,
  updateThermalCluster,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import useNavigateOnCondition from "../../../../../../../hooks/useNavigateOnCondition";
import { nameToId } from "../../../../../../../services/utils";

function ThermalForm() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { clusterId = "" } = useParams();

  useNavigateOnCondition({
    deps: [areaId],
    to: "../thermal",
  });

  // prevent re-fetch while useNavigateOnCondition event occurs
  const defaultValues = useCallback(() => {
    return getThermalCluster(study.id, areaId, clusterId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<ThermalCluster>) => {
    return updateThermalCluster(study.id, areaId, clusterId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", flexDirection: "column", overflow: "auto" }}>
      <Button
        color="secondary"
        size="small"
        onClick={() => navigate("../thermal")}
        startIcon={<ArrowBackIcon color="secondary" />}
        sx={{ alignSelf: "flex-start", mb: 1 }}
      >
        {t("button.back")}
      </Button>
      <Box sx={{ overflow: "auto" }}>
        <Form
          key={study.id + areaId}
          config={{ defaultValues }}
          onSubmit={handleSubmit}
          enableUndoRedo
        >
          <Fields />
        </Form>
        <Box
          sx={{
            width: 1,
            display: "flex",
            flexDirection: "column",
            py: 3,
            height: "75vh",
          }}
        >
          <Matrix
            study={study}
            areaId={areaId}
            clusterId={nameToId(clusterId)}
          />
        </Box>
      </Box>
    </Box>
  );
}

export default ThermalForm;
