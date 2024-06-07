import { useMemo, useState } from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import {
  Cluster,
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { COMMON_MATRIX_COLS, TS_GEN_MATRIX_COLS } from "./utils";

interface Props {
  study: StudyMetadata;
  areaId: string;
  clusterId: Cluster["id"];
}

function Matrix({ study, areaId, clusterId }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = useState("common");
  const studyVersion = Number(study.version);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const MATRICES = [
    {
      url: `input/thermal/prepro/${areaId}/${clusterId}/modulation`,
      titleKey: "common",
      columns: COMMON_MATRIX_COLS,
    },
    {
      url: `input/thermal/prepro/${areaId}/${clusterId}/data`,
      titleKey: "tsGen",
      columns: TS_GEN_MATRIX_COLS,
    },
    {
      url: `input/thermal/series/${areaId}/${clusterId}/series`,
      titleKey: "availability",
    },
    {
      url: `input/thermal/series/${areaId}/${clusterId}/fuelCost`,
      titleKey: "fuelCosts",
      minVersion: 870,
    },
    {
      url: `input/thermal/series/${areaId}/${clusterId}/CO2Cost`,
      titleKey: "co2Costs",
      minVersion: 870,
    },
  ];

  // Filter matrix data based on the study version.
  const filteredMatrices = useMemo(
    () =>
      MATRICES.filter(({ minVersion }) =>
        minVersion ? studyVersion >= minVersion : true,
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [studyVersion],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        width: 1,
        height: 1,
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
      }}
    >
      <Tabs sx={{ width: 1 }} value={value} onChange={handleTabChange}>
        {filteredMatrices.map(({ titleKey }) => (
          <Tab
            key={titleKey}
            value={titleKey}
            label={t(`study.modelization.clusters.matrix.${titleKey}`)}
          />
        ))}
      </Tabs>
      <Box sx={{ width: 1, height: 1 }}>
        {filteredMatrices.map(
          ({ url, titleKey, columns }) =>
            value === titleKey && (
              <MatrixInput
                key={titleKey}
                study={study}
                computStats={MatrixStats.NOCOL}
                url={url}
                title={t(`study.modelization.clusters.matrix.${titleKey}`)}
                columnsNames={columns}
              />
            ),
        )}
      </Box>
    </Box>
  );
}

export default Matrix;
