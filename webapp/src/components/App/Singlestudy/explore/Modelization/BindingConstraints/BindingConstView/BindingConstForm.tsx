import { AxiosError } from "axios";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Tab } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import DeleteIcon from "@mui/icons-material/Delete";
import { editStudy } from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import { BindingConstFields, ConstraintType, dataToId } from "./utils";
import {
  AllClustersAndLinks,
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../common/types";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import { ConstraintItem, ConstraintWithNullableOffset } from "./ConstraintTerm";
import { useFormContext } from "../../../../../../common/Form";
import {
  deleteConstraintTerm,
  updateConstraintTerm,
} from "../../../../../../../services/api/studydata";
import TextSeparator from "../../../../../../common/TextSeparator";
import {
  ConstraintHeader,
  ConstraintList,
  ConstraintTerm,
  MatrixContainer,
  StyledTab,
} from "./style";
import AddConstraintTermDialog from "./AddConstraintTermDialog";
import MatrixInput from "../../../../../../common/MatrixInput";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";

interface Props {
  bcIndex: number;
  study: StudyMetadata;
  bindingConst: string;
  options: AllClustersAndLinks;
}

export default function BindingConstForm(props: Props) {
  const { study, options, bindingConst, bcIndex } = props;
  const studyId = study.id;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const { control } = useFormContext<BindingConstFields>();
  const { fields, update, append, remove } = useFieldArray({
    control,
    name: "constraints",
  });

  const constraintsTerm = useMemo(
    () => fields.map((elm) => ({ ...elm, id: dataToId(elm.data) })),
    [JSON.stringify(fields)]
  );

  const pathPrefix = useMemo(
    () => `input/bindingconstraints/bindingconstraints/${bcIndex}`,
    [bcIndex]
  );

  const optionOperator = useMemo(
    () =>
      ["less", "equal", "greater", "both"].map((item) => ({
        label: t(`study.modelization.bindingConst.operator.${item}`),
        value: item.toLowerCase(),
      })),
    [t]
  );

  const typeOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly"].map((item) => ({
        label: t(`study.${item}`),
        value: item,
      })),
    [t]
  );

  const [addConstraintTermDialog, setAddConstraintTermDialog] = useState(false);
  const [termToDelete, setTermToDelete] = useState<number>();
  const [tabValue, setTabValue] = useState(0);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const saveValue = useCallback(
    async (name: string, path: string, defaultValues: any, data: any) => {
      try {
        await editStudy(data, studyId, path);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [enqueueErrorSnackbar, studyId, t]
  );

  const saveContraintValue = useCallback(
    async (
      index: number,
      prevConst: ConstraintType,
      constraint: ConstraintWithNullableOffset
    ) => {
      try {
        const tmpConst = prevConst;
        if (constraint.weight !== undefined)
          tmpConst.weight = constraint.weight;
        if (constraint.data) tmpConst.data = constraint.data;
        tmpConst.id = dataToId(tmpConst.data);
        if (constraint.offset !== undefined)
          tmpConst.offset =
            constraint.offset !== null ? constraint.offset : undefined;
        await updateConstraintTerm(study.id, bindingConst, {
          ...constraint,
          offset: tmpConst.offset,
        });
        update(index, tmpConst);
      } catch (error) {
        enqueueErrorSnackbar(
          t("study.error.updateConstraintTerm"),
          error as AxiosError
        );
      }
    },
    [bindingConst, enqueueErrorSnackbar, study.id, t, update]
  );

  const deleteTerm = useCallback(
    async (index: number) => {
      try {
        const constraintId = dataToId(constraintsTerm[index].data);
        await deleteConstraintTerm(study.id, bindingConst, constraintId);
        remove(index);
      } catch (error) {
        enqueueErrorSnackbar(
          t("study.error.deleteConstraintTerm"),
          error as AxiosError
        );
      } finally {
        setTermToDelete(undefined);
      }
    },
    [bindingConst, enqueueErrorSnackbar, constraintsTerm, remove, study.id, t]
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const jsonGenerator: IFormGenerator<BindingConstFields> = useMemo(
    () => [
      {
        translationId: "global.general",
        fields: [
          {
            type: "text",
            name: "name",
            path: `${pathPrefix}/name`,
            label: t("global.name"),
            disabled: true,
            required: t("form.field.required") as string,
          },
          {
            type: "text",
            name: "comments",
            path: `${pathPrefix}/comments`,
            label: t("study.modelization.bindingConst.comments"),
          },
          {
            type: "select",
            name: "time_step",
            path: `${pathPrefix}/type`,
            label: t("study.modelization.bindingConst.type"),
            options: typeOptions,
          },
          {
            type: "select",
            name: "operator",
            path: `${pathPrefix}/operator`,
            label: t("study.modelization.bindingConst.operator"),
            options: optionOperator,
          },
          {
            type: "switch",
            name: "enabled",
            path: `${pathPrefix}/enabled`,
            label: t("study.modelization.bindingConst.enabled"),
          },
        ],
      },
    ],
    [optionOperator, pathPrefix, t, typeOptions]
  );

  return (
    <>
      <AutoSubmitGeneratorForm
        jsonTemplate={jsonGenerator}
        saveField={saveValue}
      />
      <Box
        width="100%"
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
      >
        <StyledTab
          value={tabValue}
          onChange={handleTabChange}
          aria-label="basic tabs example"
        >
          <Tab label={t("study.modelization.bindingConst.constraintTerm")} />
          <Tab label={t("global.matrix")} />
        </StyledTab>
        <Box
          sx={{
            display: "flex",
            width: "100%",
            height: "100%",
          }}
        >
          {tabValue === 0 ? (
            <>
              <ConstraintList>
                <ConstraintHeader>
                  <Button
                    variant="text"
                    color="primary"
                    onClick={() => setAddConstraintTermDialog(true)}
                  >
                    {t("study.modelization.bindingConst.addConstraintTerm")}
                  </Button>
                </ConstraintHeader>
                {constraintsTerm.map(
                  (constraint: ConstraintType, index: number) => {
                    return index > 0 ? (
                      <ConstraintTerm key={constraint.id}>
                        <TextSeparator
                          text="+"
                          rootStyle={{ my: 0.25 }}
                          textStyle={{ fontSize: "22px" }}
                        />
                        <ConstraintItem
                          options={options}
                          saveValue={(value) =>
                            saveContraintValue(index, constraint, value)
                          }
                          constraint={constraint}
                          deleteTerm={() => setTermToDelete(index)}
                          constraintsTerm={constraintsTerm}
                        />
                      </ConstraintTerm>
                    ) : (
                      <ConstraintItem
                        key={constraint.id}
                        options={options}
                        saveValue={(value) =>
                          saveContraintValue(index, constraint, value)
                        }
                        constraint={constraint}
                        deleteTerm={() => setTermToDelete(index)}
                        constraintsTerm={constraintsTerm}
                      />
                    );
                  }
                )}
              </ConstraintList>
              {addConstraintTermDialog && (
                <AddConstraintTermDialog
                  open={addConstraintTermDialog}
                  studyId={studyId}
                  bindingConstraint={bindingConst}
                  title={t("study.modelization.bindingConst.newBindingConst")}
                  onCancel={() => setAddConstraintTermDialog(false)}
                  append={append}
                  constraintsTerm={constraintsTerm}
                  options={options}
                />
              )}
              {termToDelete !== undefined && (
                <ConfirmationDialog
                  titleIcon={DeleteIcon}
                  onCancel={() => setTermToDelete(undefined)}
                  onConfirm={() => deleteTerm(termToDelete)}
                  alert="warning"
                  open
                >
                  {t(
                    "study.modelization.bindingConst.question.deleteConstraintTerm"
                  )}
                </ConfirmationDialog>
              )}
            </>
          ) : (
            <MatrixContainer>
              <MatrixInput
                study={study}
                title={t("global.matrix")}
                url={`input/bindingconstraints/${bindingConst}`}
                computStats={MatrixStats.NOCOL}
              />
            </MatrixContainer>
          )}
        </Box>
      </Box>
    </>
  );
}
