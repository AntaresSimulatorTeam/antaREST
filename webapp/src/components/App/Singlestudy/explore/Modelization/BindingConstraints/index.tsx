import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode, useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../../common/page/NoContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import BindingConstPropsView from "./BindingConstPropsView";
import {
  getBindingConst,
  getCurrentBindingConstId,
} from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studyDataSynthesis";
import BindingConstView from "./BindingConstView";
import usePromise from "../../../../../../hooks/usePromise";
import { getBindingConstraintList } from "../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const bindingConstraints = useAppSelector((state) =>
    getBindingConst(state, study.id)
  );
  const res = usePromise(
    () => getBindingConstraintList(study.id),
    [study.id, JSON.stringify(bindingConstraints)]
  );
  const currentBindingConst = useAppSelector(getCurrentBindingConstId);
  const dispatch = useAppDispatch();

  const bcIndex = useMemo(() => {
    if (res.data)
      return res.data.findIndex((elm) => elm.id === currentBindingConst);
    return -1;
  }, [res.data, currentBindingConst]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleBindingConstClick = (bindingConstId: string): void => {
    dispatch(setCurrentBindingConst(bindingConstId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <UsePromiseCond
          response={res}
          ifPending={() => <SimpleLoader />}
          ifResolved={(data) => (
            <Box width="100%" height="100%">
              <BindingConstPropsView
                onClick={handleBindingConstClick}
                list={data || []}
                studyId={study.id}
                currentBindingConst={currentBindingConst || undefined}
              />
            </Box>
          )}
        />
      }
      right={
        <>
          {R.cond([
            // Binding constraints list
            [
              () => currentBindingConst !== undefined && res.data !== undefined,
              () =>
                (
                  <BindingConstView
                    bindingConst={currentBindingConst}
                    bcIndex={bcIndex}
                  />
                ) as ReactNode,
            ],
            // No Areas
            [
              R.T,
              () => (<NoContent title="No Binding Constraints" />) as ReactNode,
            ],
          ])()}
        </>
      }
    />
  );
}

export default BindingConstraints;
