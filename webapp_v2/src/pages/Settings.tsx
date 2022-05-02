import SettingsIcon from "@mui/icons-material/Settings";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import { SyntheticEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import RootPage from "../components/common/page/RootPage";
import Groups from "../components/settings/Groups";
import Users from "../components/settings/Users";
import { isAuthUserAdmin, isAuthUserInGroupAdmin } from "../store/selectors";

/**
 * Component
 */

function Settings() {
  const [tabValue, setTabValue] = useState("1");
  const [t] = useTranslation();
  const isUserAdmin = useSelector(isAuthUserAdmin);
  const isUserInGroupAdmin = useSelector(isAuthUserInGroupAdmin);

  const tabList = useMemo(() => {
    return [
      isUserAdmin && [t("settings:users"), () => <Users />],
      (isUserAdmin || isUserInGroupAdmin) && [
        t("settings:groups"),
        () => <Groups />,
      ],
      [t("settings:tokens"), () => "Tokens"],
      isUserAdmin && [t("settings:maintenance"), () => "Maintenance"],
    ].filter(Boolean) as Array<[string, () => JSX.Element]>;
  }, [isUserAdmin, isUserInGroupAdmin, t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTabChange = (event: SyntheticEvent, newValue: string) => {
    setTabValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabContext value={tabValue}>
      <RootPage
        title={t("main:settings")}
        titleIcon={SettingsIcon}
        headerBottom={
          <Box
            sx={{
              width: 1,
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
            <TabList onChange={handleTabChange}>
              {tabList.map(([label], index) => (
                <Tab key={label} label={label} value={String(index + 1)} />
              ))}
            </TabList>
          </Box>
        }
        hideHeaderDivider
      >
        {tabList.map(([label, Element], index) => (
          <TabPanel
            sx={{
              paddingTop: 0,
              paddingBottom: 0,
              overflow: "auto",
            }}
            key={label}
            value={String(index + 1)}
          >
            <Element />
          </TabPanel>
        ))}
      </RootPage>
    </TabContext>
  );
}

export default Settings;
