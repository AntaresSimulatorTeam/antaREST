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

import {
  createTheme,
  CssBaseline,
  StyledEngineProvider,
  ThemeProvider,
  useMediaQuery,
  type PaletteMode,
  Box,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { deepmerge } from "@mui/utils";
import { baseTheme, lightPalette, darkPalette } from "./theme";
import topRightBg from "../../../assets/img/top-right-background.png";
import "./index.css";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";

declare module "@mui/material/styles" {
  interface Theme {
    setThemeMode: React.Dispatch<React.SetStateAction<PaletteMode>>;
  }
}

function ThemeWrapper({ children }: { children: React.ReactNode }) {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const [themeMode, setThemeMode] = useState<PaletteMode>(prefersDarkMode ? "dark" : "light");

  const theme = useMemo(() => {
    return createTheme(
      deepmerge(baseTheme, {
        palette: {
          ...(themeMode === "light" ? lightPalette : darkPalette),
          mode: themeMode,
        },
        setThemeMode,
      }),
    );
  }, [themeMode]);

  useEffect(() => {
    setThemeMode(prefersDarkMode ? "dark" : "light");
  }, [prefersDarkMode]);

  return (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            background: `url(${topRightBg}) top right / 40% no-repeat `,
          }}
        >
          {children}
        </Box>
      </ThemeProvider>
    </StyledEngineProvider>
  );
}

export default ThemeWrapper;
