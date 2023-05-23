import {
  BatchFieldArrayUpdate,
  FieldPath,
  FieldValue,
  FieldValues,
  Path,
  UseFormReturn,
  UseFormSetValue,
  UseFormUnregister,
} from "react-hook-form";
import * as RA from "ramda-adjunct";
import { MutableRefObject, useEffect, useMemo } from "react";
import useAutoUpdateRef from "../../../hooks/useAutoUpdateRef";
import {
  UseFormRegisterPlus,
  UseFormReturnPlus,
  UseFormSetValues,
  AutoSubmitHandler,
} from "./types";

interface Params<TFieldValues extends FieldValues, TContext> {
  formApi: UseFormReturn<TFieldValues, TContext>;
  isAutoSubmitEnabled: boolean;
  fieldAutoSubmitListeners: MutableRefObject<
    Record<string, AutoSubmitHandler<FieldValue<TFieldValues>> | undefined>
  >;
  fieldsChangeDuringAutoSubmitting: MutableRefObject<FieldPath<TFieldValues>[]>;
  submit: VoidFunction;
}

function useFormApiPlus<TFieldValues extends FieldValues, TContext>(
  params: Params<TFieldValues, TContext>
): UseFormReturnPlus<TFieldValues, TContext> {
  const {
    formApi,
    fieldAutoSubmitListeners,
    fieldsChangeDuringAutoSubmitting,
    ...data
  } = params;
  const { register, unregister, getValues, setValue, control } = formApi;
  // Prevent to add the values in `useMemo`'s deps
  const dataRef = useAutoUpdateRef({
    ...data,
    // Don't read `formState` in `useMemo`. See `useEffect`'s comment below.
    isSubmitting: formApi.formState.isSubmitting,
  });

  const formApiPlus = useMemo(
    () => {
      const registerWrapper: UseFormRegisterPlus<TFieldValues> = (
        name,
        options
      ) => {
        if (options?.onAutoSubmit) {
          fieldAutoSubmitListeners.current[name] = options.onAutoSubmit;
        }

        const newOptions: typeof options = {
          ...options,
          onChange: (event: unknown) => {
            options?.onChange?.(event);

            if (dataRef.current.isAutoSubmitEnabled) {
              if (
                dataRef.current.isSubmitting &&
                !fieldsChangeDuringAutoSubmitting.current.includes(name)
              ) {
                fieldsChangeDuringAutoSubmitting.current.push(name);
              }

              dataRef.current.submit();
            }
          },
        };

        return register(name, newOptions);
      };

      const unregisterWrapper: UseFormUnregister<TFieldValues> = (
        name,
        options
      ) => {
        if (dataRef.current.isAutoSubmitEnabled) {
          const names = RA.ensureArray(name) as Path<TFieldValues>[];
          names.forEach((n) => {
            delete fieldAutoSubmitListeners.current[n];
          });
        }
        return unregister(name, options);
      };

      const setValueWrapper: UseFormSetValue<TFieldValues> = (
        name,
        value,
        options
      ) => {
        const newOptions: typeof options = {
          shouldDirty: true, // False by default
          ...options,
        };

        if (dataRef.current.isAutoSubmitEnabled && newOptions.shouldDirty) {
          if (dataRef.current.isSubmitting) {
            fieldsChangeDuringAutoSubmitting.current.push(name);
          }
          // If it's a new value
          if (value !== getValues(name)) {
            dataRef.current.submit();
          }
        }

        setValue(name, value, newOptions);
      };

      const setValues: UseFormSetValues<TFieldValues> = (values, options) => {
        Object.keys(values).forEach((name) => {
          setValueWrapper(name as Path<TFieldValues>, values[name], options);
        });
      };

      const updateFieldArrayWrapper: BatchFieldArrayUpdate = (...args) => {
        control._updateFieldArray(...args);
        if (dataRef.current.isAutoSubmitEnabled) {
          dataRef.current.submit();
        }
      };

      // Spreading cannot be used because getters and setters would be removed
      const controlPlus = new Proxy(control, {
        // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
        get(...args) {
          const prop = args[1];
          if (prop === "register") {
            return registerWrapper;
          }
          if (prop === "unregister") {
            return unregisterWrapper;
          }
          if (prop === "_updateFieldArray") {
            return updateFieldArrayWrapper;
          }
          return Reflect.get(...args);
        },
      });

      return {
        ...formApi,
        setValues,
        register: registerWrapper,
        unregister: unregisterWrapper,
        setValue: setValueWrapper,
        control: controlPlus,
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [formApi]
  );

  // `formState` is wrapped with a Proxy and updated in batch.
  // The API is updated here to keep reference, like `useForm` return.
  useEffect(() => {
    formApiPlus.formState = formApi.formState;
  }, [formApiPlus, formApi.formState]);

  return formApiPlus;
}

export default useFormApiPlus;
