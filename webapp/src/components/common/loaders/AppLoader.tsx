/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Typography } from "@mui/material";
import logo from "../../../assets/img/logo.png";
import topRightBackground from "../../../assets/img/top-right-background.png";

function AppLoader() {
  const [t] = useTranslation();
  const [value, setValue] = useState<number>(0);
  const maxValue = 4;
  const timeDelay = 300;

  useEffect(() => {
    const interval = setInterval(() => {
      setValue((val) => (val + 1) % maxValue);
    }, timeDelay);
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);

  return (
    <Box
      display="flex"
      height="100vh"
      sx={{
        background: "radial-gradient(ellipse at top right, #190520 0%, #190520 30%, #222333 100%)",
      }}
    >
      <Box
        position="absolute"
        top="0px"
        right="0px"
        display="flex"
        justifyContent="center"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <img src={topRightBackground} alt="logo" style={{ height: "auto" }} />
      </Box>
      <Box flexGrow={1} display="flex" alignItems="center" justifyContent="center" zIndex={999}>
        <Box
          width="400px"
          display="flex"
          justifyContent="center"
          alignItems="center"
          flexDirection="column"
        >
          <Box
            display="flex"
            width="100%"
            justifyContent="center"
            alignItems="center"
            flexDirection="column"
            flexWrap="nowrap"
            boxSizing="border-box"
          >
            <img src={logo} alt="logo" style={{ height: "96px" }} />
            <Typography variant="h4" component="h4" color="primary" my={2}>
              Antares Web
            </Typography>
          </Box>
          <Typography sx={{ my: 3 }}>{`${t("global.loading")}${Array(value)
            .fill(0)
            .map((elm) => ".")
            .join("")}`}</Typography>
        </Box>
      </Box>
    </Box>
  );
}

export default AppLoader;
