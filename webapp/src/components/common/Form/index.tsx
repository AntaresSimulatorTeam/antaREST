/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  DeepPartial,
  FieldPath,
  FieldValues,
  FormProvider,
  FormState,
  SubmitErrorHandler,
  useForm,
  useFormContext as useFormContextOriginal,
  UseFormProps,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import * as RA from "ramda-adjunct";
import {
  Box,
  CircularProgress,
  Divider,
  IconButton,
  setRef,
  SxProps,
  Theme,
  Tooltip,
} from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";
import { useUpdateEffect } from "react-use";
import * as R from "ramda";
import clsx from "clsx";
import { LoadingButton, LoadingButtonProps } from "@mui/lab";
import UndoIcon from "@mui/icons-material/Undo";
import RedoIcon from "@mui/icons-material/Redo";
import axios from "axios";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import useDebounce from "../../../hooks/useDebounce";
import {
  ROOT_ERROR_KEY,
  getDirtyValues,
  stringToPath,
  toAutoSubmitConfig,
} from "./utils";
import useDebouncedState from "../../../hooks/useDebouncedState";
import usePrompt from "../../../hooks/usePrompt";
import { SubmitHandlerPlus, UseFormReturnPlus } from "./types";
import FormContext from "./FormContext";
import useFormApiPlus from "./useFormApiPlus";
import useFormUndoRedo from "./useFormUndoRedo";
import { mergeSxProp } from "../../../utils/muiUtils";

export interface AutoSubmitConfig {
  enable: boolean;
  wait?: number;
}

export interface FormProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any,
  SubmitReturnValue = any,
> extends Omit<
    React.HTMLAttributes<HTMLFormElement>,
    "onSubmit" | "onInvalid" | "children"
  > {
  config?: UseFormProps<TFieldValues, TContext>;
  onSubmit?: (
    data: SubmitHandlerPlus<TFieldValues>,
    event?: React.BaseSyntheticEvent,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (
    data: SubmitHandlerPlus<TFieldValues>,
    submitResult: SubmitReturnValue,
  ) => void;
  onInvalid?: SubmitErrorHandler<TFieldValues>;
  children:
    | ((formApi: UseFormReturnPlus<TFieldValues, TContext>) => React.ReactNode)
    | React.ReactNode;
  submitButtonText?: string;
  submitButtonIcon?: LoadingButtonProps["startIcon"];
  miniSubmitButton?: boolean;
  hideSubmitButton?: boolean;
  hideFooterDivider?: boolean;
  onStateChange?: (state: FormState<TFieldValues>) => void;
  autoSubmit?: boolean | AutoSubmitConfig;
  enableUndoRedo?: boolean;
  sx?: SxProps<Theme>;
  apiRef?: React.Ref<UseFormReturnPlus<TFieldValues, TContext> | undefined>;
}

export function useFormContextPlus<TFieldValues extends FieldValues>() {
  return useFormContextOriginal() as UseFormReturnPlus<TFieldValues>;
}

function Form<TFieldValues extends FieldValues, TContext>(
  props: FormProps<TFieldValues, TContext>,
) {
  const {
    config,
    onSubmit,
    onSubmitSuccessful,
    onInvalid,
    children,
    submitButtonText,
    submitButtonIcon = <SaveIcon />,
    miniSubmitButton,
    hideSubmitButton,
    hideFooterDivider,
    onStateChange,
    autoSubmit,
    enableUndoRedo,
    className,
    sx,
    apiRef,
    ...formProps
  } = props;

  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const autoSubmitConfig = toAutoSubmitConfig(autoSubmit);

  const [isInProgress, setIsInProgress] = useState(false);
  const [showAutoSubmitLoader, setShowAutoSubmitLoader] = useDebouncedState(
    false,
    750,
  );

  const fieldAutoSubmitListeners = useRef<
    Record<string, ((v: any) => any | Promise<any>) | undefined>
  >({});
  const fieldsChangeDuringAutoSubmitting = useRef<
    Array<FieldPath<TFieldValues>>
  >([]);
  const lastSubmittedData = useRef<TFieldValues>();
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  const submitSuccessfulCb = useRef(() => {});

  const contextValue = useMemo(
    () => ({ isAutoSubmitEnabled: autoSubmitConfig.enable }),
    [autoSubmitConfig.enable],
  );

  const formApi = useForm<TFieldValues, TContext>({
    mode: "onChange",
    delayError: 750,
    ...config,
    defaultValues: RA.isFunction(config?.defaultValues)
      ? () => {
          const fn = config?.defaultValues as () => Promise<TFieldValues>;
          return fn().catch((err) => {
            enqueueErrorSnackbar(t("form.asyncDefaultValues.error"), err);
            throw err;
          });
        }
      : config?.defaultValues,
  });

  const { getValues, setValue, setError, handleSubmit, formState, reset } =
    formApi;
  // * /!\ `formState` is a proxy
  const { isSubmitting, isSubmitSuccessful, isDirty, dirtyFields, errors } =
    formState;
  // Don't add `isValid` because we need to trigger fields validation.
  // In case we have invalid default value for example.
  const isSubmitAllowed = isDirty && !isSubmitting;
  const rootError = errors.root?.[ROOT_ERROR_KEY];
  const showSubmitButton = !hideSubmitButton && !autoSubmitConfig.enable;
  const showFooter = showSubmitButton || enableUndoRedo || rootError;

  const formApiPlus = useFormApiPlus({
    formApi,
    isAutoSubmitEnabled: autoSubmitConfig.enable,
    fieldAutoSubmitListeners,
    fieldsChangeDuringAutoSubmitting,
    // eslint-disable-next-line no-use-before-define
    submit: () => requestSubmit(),
  });

  const { set, undo, redo, canUndo, canRedo } = useFormUndoRedo(formApiPlus);

  // Auto Submit Loader
  useEffect(
    () => {
      if (autoSubmitConfig.enable) {
        setShowAutoSubmitLoader(isSubmitting);
        // Show the loader immediately when the form is submitting
        if (isSubmitting) {
          setShowAutoSubmitLoader.flush();
        }
      } else if (showAutoSubmitLoader) {
        setShowAutoSubmitLoader(false);
        setShowAutoSubmitLoader.flush();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isSubmitting, autoSubmitConfig.enable],
  );

  // Reset after successful submit.
  // It's recommended to reset inside useEffect after submission: https://react-hook-form.com/api/useform/reset
  useEffect(
    () => {
      if (isSubmitSuccessful && lastSubmittedData.current) {
        submitSuccessfulCb.current();

        const valuesToSetAfterReset = getValues(
          fieldsChangeDuringAutoSubmitting.current,
        );

        // Reset only dirty values make issue with `getValues` and `watch` which only return reset values
        reset(lastSubmittedData.current);
        set(lastSubmittedData.current);

        fieldsChangeDuringAutoSubmitting.current.forEach((fieldName, index) => {
          setValue(fieldName, valuesToSetAfterReset[index], {
            shouldDirty: true,
          });
        });

        fieldsChangeDuringAutoSubmitting.current = [];
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isSubmitSuccessful],
  );

  // Prevent browser close if a submit is pending
  useEffect(() => {
    const listener = (event: BeforeUnloadEvent) => {
      if (isInProgress) {
        // eslint-disable-next-line no-param-reassign
        event.returnValue = t("form.submit.inProgress");
      } else if (isDirty) {
        // eslint-disable-next-line no-param-reassign
        event.returnValue = t("form.changeNotSaved");
      }
    };

    window.addEventListener("beforeunload", listener);

    return () => {
      window.removeEventListener("beforeunload", listener);
    };
  }, [t, isInProgress, isDirty]);

  useUpdateEffect(() => onStateChange?.(formState), [formState]);

  useEffect(() => setRef(apiRef, formApiPlus));

  usePrompt(t("form.submit.inProgress"), isInProgress);
  usePrompt(t("form.changeNotSaved"), isDirty && !isInProgress);

  ////////////////////////////////////////////////////////////////
  // Submit
  ////////////////////////////////////////////////////////////////

  const submit = () => {
    const callback = handleSubmit(function onValid(data, event) {
      lastSubmittedData.current = data;

      const dirtyValues = getDirtyValues(dirtyFields, data) as DeepPartial<
        typeof data
      >;

      const toResolve = [];

      if (autoSubmitConfig.enable) {
        const listeners = fieldAutoSubmitListeners.current;
        toResolve.push(
          ...Object.keys(listeners)
            .filter((key) => R.hasPath(stringToPath(key), dirtyValues))
            .map((key) => {
              const listener = fieldAutoSubmitListeners.current[key];
              return listener?.(R.path(stringToPath(key), data));
            }),
        );
      }

      const dataArg = { values: data, dirtyValues };

      if (onSubmit) {
        toResolve.push(onSubmit(dataArg, event));
      }

      return Promise.all(toResolve)
        .then((values) => {
          submitSuccessfulCb.current = () => {
            const onSubmitRes = onSubmit ? R.last(values) : undefined;
            onSubmitSuccessful?.(dataArg, onSubmitRes);
          };
        })
        .catch((err) => {
          enqueueErrorSnackbar(t("form.submit.error"), err);

          // Any error under the `root` key are not persisted with each submission.
          // They will be deleted automatically.
          // cf. https://www.react-hook-form.com/api/useform/seterror/
          setError(`root.${ROOT_ERROR_KEY}`, {
            message: axios.isAxiosError(err)
              ? err.response?.data.description
              : err?.toString(),
          });
        })
        .finally(() => {
          setIsInProgress(false);
        });
    }, onInvalid);

    return callback();
  };

  const submitDebounced = useDebounce(submit, autoSubmitConfig.wait);

  const requestSubmit = () => {
    setIsInProgress(true);

    if (autoSubmitConfig.enable) {
      submitDebounced();
    } else {
      submit();
    }
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    requestSubmit();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      {...formProps}
      sx={mergeSxProp(
        {
          display: "flex",
          flexDirection: "column",
          height: 1,
          overflow: "auto",
        },
        sx,
      )}
      component="form"
      onSubmit={handleFormSubmit}
      className={clsx("Form", className)}
    >
      {showAutoSubmitLoader && (
        <Box
          className="Form__Loader"
          sx={{
            position: "sticky",
            top: 0,
            right: 0,
            height: 0,
            textAlign: "right",
          }}
        >
          <CircularProgress color="secondary" size={20} sx={{ mr: 1 }} />
        </Box>
      )}
      <Box className="Form__Content" sx={{ overflow: "auto" }}>
        <FormContext.Provider value={contextValue}>
          {RA.isFunction(children) ? (
            children(formApiPlus)
          ) : (
            <FormProvider {...formApiPlus}>{children}</FormProvider>
          )}
        </FormContext.Provider>
      </Box>
      {showFooter && (
        <Box
          className="Form__Footer"
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 1.5,
            mt: hideFooterDivider ? 0 : 1.5,
          }}
        >
          {!hideFooterDivider && <Divider flexItem />}
          {rootError && (
            <Box color="error.main" sx={{ fontSize: "0.9rem" }}>
              {rootError.message || t("form.submit.error")}
            </Box>
          )}
          <Box className="Form__Footer__Actions" sx={{ display: "flex" }}>
            {showSubmitButton && (
              <>
                <LoadingButton
                  type="submit"
                  size="small"
                  disabled={!isSubmitAllowed}
                  loading={isSubmitting}
                  {...(miniSubmitButton
                    ? {
                        children: submitButtonIcon,
                      }
                    : {
                        loadingPosition: "start",
                        startIcon: submitButtonIcon,
                        variant: "contained",
                        children: submitButtonText || t("global.save"),
                      })}
                />
                {enableUndoRedo && (
                  <Divider sx={{ mx: 2 }} orientation="vertical" flexItem />
                )}
              </>
            )}
            {enableUndoRedo && (
              <>
                <Tooltip title={t("global.undo")}>
                  <span>
                    <IconButton size="small" onClick={undo} disabled={!canUndo}>
                      <UndoIcon />
                    </IconButton>
                  </span>
                </Tooltip>
                <Tooltip title={t("global.redo")}>
                  <span>
                    <IconButton size="small" onClick={redo} disabled={!canRedo}>
                      <RedoIcon />
                    </IconButton>
                  </span>
                </Tooltip>
              </>
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
}

export default Form;
