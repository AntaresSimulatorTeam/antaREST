import { useTranslation } from "react-i18next";
import TableForm from "../../../../../../../common/TableForm";
import {
  GenericScenarioConfig,
  ScenarioType,
  ClustersHandlerReturn,
  updateScenarioBuilderConfig,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import EmptyView from "../../../../../../../common/page/SimpleContent";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../../../../../../utils/fnUtils";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";

interface Props {
  config: GenericScenarioConfig | ClustersHandlerReturn;
  type: ScenarioType;
  areaId?: string;
}

function Table({ config, type, areaId }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus) => {
    const updatedScenario = {
      [type]:
        (type === "thermal" || type === "renewable") && areaId
          ? { [areaId]: dirtyValues }
          : dirtyValues,
    };

    try {
      await updateScenarioBuilderConfig(study.id, updatedScenario, type);
    } catch (error) {
      enqueueErrorSnackbar(
        t("study.configuration.general.mcScenarioBuilder.update.error", {
          type,
        }),
        toError(error),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (Object.keys(config).length === 0) {
    return <EmptyView title="No scenario configuration." />;
  }

  return (
    <TableForm
      key={JSON.stringify(config)}
      autoSubmit={false}
      defaultValues={config}
      tableProps={{
        type: "numeric",
        placeholder: "rand",
        allowEmpty: true,
        colHeaders: (index) =>
          `${t("study.configuration.general.mcScenarioBuilder.year")} ${
            index + 1
          }`,
        className: "htCenter",
      }}
      onSubmit={handleSubmit}
    />
  );
}

export default Table;
