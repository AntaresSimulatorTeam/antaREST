import { DependencyList, useCallback, useEffect, useState } from "react";

export interface UsePromiseResponse<T> {
  data: T | undefined;
  isLoading: boolean;
  error: Error | string | undefined;
  reload: () => void;
}

export interface UsePromiseParams {
  resetDataOnReload?: boolean;
}

function usePromise<T, U extends UsePromiseParams>(
  fn: () => Promise<T>,
  params?: U,
  deps: DependencyList = []
): UsePromiseResponse<T> {
  const [data, setData] = useState<T>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | string | undefined>();
  const [reloadCount, setReloadCount] = useState(0);
  const reload = useCallback(() => setReloadCount((prev) => prev + 1), []);

  const resetDataOnReload =
    params?.resetDataOnReload === undefined ? true : params?.resetDataOnReload;

  useEffect(
    () => {
      let isMounted = true;

      setIsLoading(true);
      // Reset
      if (resetDataOnReload) {
        setData(undefined);
      }
      setError(undefined);

      fn()
        .then((res) => {
          if (isMounted) {
            setData(res);
          }
        })
        .catch((err) => {
          if (isMounted) {
            setError(err);
          }
        })
        .finally(() => {
          if (isMounted) {
            setIsLoading(false);
          }
        });

      return () => {
        isMounted = false;
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [reloadCount, ...deps]
  );

  return { data, isLoading, error, reload };
}

export default usePromise;
