import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useOutletContext } from "react-router";
import { AxiosError } from "axios";
import { useMemo } from "react";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { StudyMetadata } from "../../../../../../../../common/types";
import { createStudyMapLayer } from "../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getStudyMapLayers } from "../../../../../../../../redux/selectors";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  name: "",
};

function CreateLayerDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const layers = useAppSelector(getStudyMapLayers);

  const existingLayers = useMemo(
    () => Object.values(layers).map((layer) => layer.name),
    [layers]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    try {
      dispatch(
        createStudyMapLayer({ studyId: study.id, name: data.values.name })
      );
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createLayer"), e as AxiosError);
    }

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title="Add new layer"
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control }) => (
        <StringFE
          label={t("global.name")}
          name="name"
          control={control}
          fullWidth
          rules={{
            required: { value: true, message: t("form.field.required") },
            validate: (layer) => {
              if (layer.trim().length <= 0) {
                return false;
              }
              if (existingLayers.includes(layer)) {
                return `The layer ${layer} already exists`;
              }
            },
          }}
        />
      )}
    </FormDialog>
  );
}

export default CreateLayerDialog;
