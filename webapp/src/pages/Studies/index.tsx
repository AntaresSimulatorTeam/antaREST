import { useState } from "react";
import * as R from "ramda";
import { Box, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import SideNav from "../../components/studies/SideNav";
import StudiesList from "../../components/studies/StudiesList";
import { fetchStudies } from "../../redux/ducks/studies";
import RootPage from "../../components/common/page/RootPage";
import HeaderTopRight from "../../components/studies/HeaderTopRight";
import HeaderBottom from "../../components/studies/HeaderBottom";
import SimpleLoader from "../../components/common/loaders/SimpleLoader";
import {
  getStudiesState,
  getStudyIdsFilteredAndSorted,
} from "../../redux/selectors";
import { FetchStatus } from "../../redux/utils";
import useAsyncAppSelector from "../../redux/hooks/useAsyncAppSelector";
import FilterDrawer from "../../components/studies/FilterDrawer";

function Studies() {
  const [t] = useTranslation();
  const studiesFilteredAndSorted = useAsyncAppSelector({
    entityStateSelector: getStudiesState,
    fetchAction: fetchStudies,
    valueSelector: getStudyIdsFilteredAndSorted,
  });
  const [openFilter, setOpenFilter] = useState(false);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage
      title={t("global.studies")}
      titleIcon={TravelExploreOutlinedIcon}
      headerTopRight={<HeaderTopRight />}
      headerBottom={
        <HeaderBottom onOpenFilterClick={() => setOpenFilter(true)} />
      }
    >
      <Box
        sx={{
          flex: 1,
          width: 1,
          display: "flex",
          flexDirection: "row",
          justifyContent: "flex-start",
          alignItems: "flex-start",
          boxSizing: "border-box",
        }}
      >
        <SideNav />
        <Divider sx={{ width: "1px", height: "98%", bgcolor: "divider" }} />
        {R.cond([
          [R.equals(FetchStatus.Loading), () => <SimpleLoader />],
          [
            R.equals(FetchStatus.Succeeded),
            () => <StudiesList studyIds={studiesFilteredAndSorted.value} />,
          ],
          [
            R.equals(FetchStatus.Failed),
            () => {
              // TODO
              return <div>Error</div>;
            },
          ],
        ])(studiesFilteredAndSorted.status)}
        <FilterDrawer open={openFilter} onClose={() => setOpenFilter(false)} />
      </Box>
    </RootPage>
  );
}

export default Studies;
