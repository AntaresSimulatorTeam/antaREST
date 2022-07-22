import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import ClusterRoot from "../common/ClusterRoot";
import RenewableForm from "./RenewableForm";
import { getDefaultValues } from "./utils";

function Renewables() {
  const fixedGroupList = [
    "Wind Onshore",
    "Wind Offshore",
    "Solar Thermal",
    "Solar PV",
    "Solar Rooftop",
    "Other RES 1",
    "Other RES 2",
    "Other RES 3",
    "Other RES 4",
  ];
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  return (
    <ClusterRoot
      study={study}
      fixedGroupList={fixedGroupList}
      type="renewables"
      getDefaultValues={getDefaultValues}
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ study, cluster, area, groupList }) => (
        <RenewableForm
          study={study}
          cluster={cluster}
          area={area}
          groupList={groupList}
        />
      )}
    </ClusterRoot>
  );
}

export default Renewables;
