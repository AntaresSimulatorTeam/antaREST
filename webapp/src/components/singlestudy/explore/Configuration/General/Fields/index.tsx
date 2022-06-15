import * as R from "ramda";
import { Box, Divider, TextField } from "@mui/material";
import { useEffect } from "react";
import { StyledFieldset } from "../styles";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import { StudyMetadata } from "../../../../../../common/types";
import { editStudy } from "../../../../../../services/api/study";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import {
  FIRST_JANUARY_OPTIONS,
  FormValues,
  WEEK_OPTIONS,
  YEAR_OPTIONS,
} from "../utils";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import { useFormContext } from "../../../../../common/Form";

interface Props {
  study: StudyMetadata;
}

// TODO i18n

function Fields(props: Props) {
  const { study } = props;
  const studyVersion = Number(study.version);
  const { register, setValue, watch, getValues } = useFormContext<FormValues>();
  const buildingMode = watch("buildingMode");

  useEffect(() => {
    if (buildingMode === "Derated") {
      setValue("nbYears", 1);
    }
  }, [buildingMode, setValue]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDayValidation = (v: number) => {
    if (v === 0 || Number.isNaN(v)) {
      return "Minimum is 1";
    }
    if (getValues("firstDay") > getValues("lastDay")) {
      return "First day must be lower or equal to last day";
    }
    if (getValues("leapYear")) {
      return v <= 365 ? true : "Maximum is 365 for a leap year";
    }
    return v <= 364 ? true : "Maximum is 364 for a non-leap year";
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const saveValue = R.curry((path: string, value) => {
    return editStudy(value, study.id, `settings/generaldata/${path}`);
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <StyledFieldset legend="Simulation">
        <SelectFE
          label="Mode"
          options={["Economy", "Adequacy", "draft"]}
          {...register("mode", {
            onAutoSubmit: saveValue("general/mode"),
          })}
        />
        <TextField
          label="First day"
          variant="filled"
          {...register("firstDay", {
            deps: "lastDay",
            valueAsNumber: true,
            validate: handleDayValidation,
            onAutoSubmit: saveValue("general/simulation.start"),
          })}
        />
        <TextField
          label="Last day"
          variant="filled"
          {...register("lastDay", {
            deps: "firstDay",
            valueAsNumber: true,
            validate: handleDayValidation,
            onAutoSubmit: saveValue("general/simulation.end"),
          })}
        />
      </StyledFieldset>
      <StyledFieldset legend="Calendar">
        <TextField
          label="Horizon"
          variant="filled"
          {...register("horizon", {
            onAutoSubmit: saveValue("general/horizon"),
          })}
        />
        <SelectFE
          label="Year"
          options={YEAR_OPTIONS}
          {...register("firstMonth", {
            onAutoSubmit: saveValue("general/first-month-in-year"),
          })}
        />
        <SelectFE
          label="Week"
          options={WEEK_OPTIONS}
          {...register("firstWeekDay", {
            onAutoSubmit: saveValue("general/first.weekday"),
          })}
        />
        <SelectFE
          label="1st January"
          options={FIRST_JANUARY_OPTIONS}
          {...register("firstJanuary", {
            onAutoSubmit: saveValue("general/january.1st"),
          })}
        />
        <SwitchFE
          sx={{ flex: 1, flexBasis: "100%" }}
          label="Leap year"
          {...register("leapYear", {
            deps: ["firstDay", "lastDay"],
            onAutoSubmit: saveValue("general/leapyear"),
          })}
        />
      </StyledFieldset>
      <Box sx={{ display: "flex" }}>
        <StyledFieldset
          legend="Monte-Carlo Scenarios"
          sx={{
            flex: 1,
          }}
          contentProps={{
            sx: { flexDirection: "column" },
          }}
        >
          <TextField
            label="Number"
            variant="filled"
            {...register("nbYears", {
              validate: (v) => {
                if (buildingMode === "Derated") {
                  return v === 1
                    ? true
                    : "Value must be 1 when building mode is derated";
                }
                if (v === 0) {
                  return "Minimum is 1";
                }
                return v <= 50000 ? true : "Maximum is 50000";
              },
              valueAsNumber: true,
              onAutoSubmit: saveValue("general/nbyears"),
            })}
          />
          <SelectFE
            label="Building mode"
            options={["Automatic", "Custom", "Derated"]}
            {...register("buildingMode", {
              deps: "nbYears",
              onAutoSubmit: (v) => {
                if (v === "Derated") {
                  return saveValue("general/derated", true);
                }
                return Promise.all([
                  saveValue(
                    studyVersion >= 800
                      ? "general/custom-scenarios"
                      : "general/custom-ts-numbers",
                    v === "Custom"
                  ),
                  saveValue("general/derated", false),
                ]);
              },
            })}
          />
          <BooleanFE
            label="Selection mode"
            trueText="Custom"
            falseText="Automatic"
            {...register("selectionMode", {
              onAutoSubmit: saveValue("general/user-playlist"),
            })}
          />
        </StyledFieldset>
        <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />
        <StyledFieldset
          legend="Output profile"
          sx={{
            flex: 1,
          }}
          contentProps={{
            sx: { flexDirection: "column" },
          }}
        >
          <SwitchFE
            label="Simulation synhtesis"
            {...register("simulationSynthesis", {
              onAutoSubmit: saveValue("output/synthesis"),
            })}
          />
          <SwitchFE
            label="Year-by-year"
            {...register("yearByYear", {
              onAutoSubmit: saveValue("general/year-by-year"),
            })}
          />
          <SwitchFE
            label="MC Scenario"
            {...register("mcScenario", {
              onAutoSubmit: saveValue("output/storenewset"),
            })}
          />
          {studyVersion >= 710 ? (
            <>
              <BooleanFE
                label="Geographic trimming"
                trueText="None"
                falseText="Custom"
                {...register("geographicTrimming", {
                  onAutoSubmit: saveValue("general/geographic-trimming"),
                })}
              />
              <BooleanFE
                label="Thematic trimming"
                trueText="None"
                falseText="Custom"
                {...register("thematicTrimming", {
                  onAutoSubmit: saveValue("general/thematic-trimming"),
                })}
              />
            </>
          ) : (
            <SwitchFE
              label="Filtering"
              {...register("filtering", {
                onAutoSubmit: saveValue("general/filtering"),
              })}
            />
          )}
        </StyledFieldset>
      </Box>
    </>
  );
}

export default Fields;
