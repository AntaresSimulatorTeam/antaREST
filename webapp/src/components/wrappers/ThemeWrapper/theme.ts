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

import type { PaletteOptions, ThemeOptions } from "@mui/material";

const SECONDARY_MAIN_COLOR = "#00B2FF";

export const baseTheme: ThemeOptions = {
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        "&::-webkit-scrollbar": {
          width: "7px",
          height: "7px",
        },
        "&::-webkit-scrollbar-track": {
          boxShadow: "inset 0 0 6px rgba(0, 0, 0, 0.3)",
        },
        "&::-webkit-scrollbar-thumb": {
          backgroundColor: SECONDARY_MAIN_COLOR,
        },
      },
    },
    MuiFormControl: {
      defaultProps: {
        margin: "dense", // Prevent label from being cut
      },
    },
    MuiAutocomplete: {
      defaultProps: {
        size: "small",
      },
    },
    MuiButton: {
      defaultProps: {
        size: "small",
      },
    },
    MuiButtonGroup: {
      defaultProps: {
        size: "small",
      },
    },
    MuiCheckbox: {
      defaultProps: {
        size: "small",
      },
    },
    MuiInputBase: {
      defaultProps: {
        size: "small",
      },
    },
    MuiInputLabel: {
      defaultProps: {
        shrink: true,
      },
    },
    MuiOutlinedInput: {
      defaultProps: {
        notched: true, // Fix for empty field with `shrink` to true
      },
    },
    MuiSvgIcon: {
      defaultProps: {
        fontSize: "small",
      },
    },
    MuiChip: {
      defaultProps: {
        size: "small",
      },
    },
  },
};

export const lightPalette: PaletteOptions = {
  // palette values for light mode
  // primary: amber,
  // divider: amber[200],
  // text: {
  //   primary: grey[900],
  //   secondary: grey[800],
  // },
};

export const darkPalette: PaletteOptions = {
  //primary: "",
  //secondary?: PaletteColorOptions;
  //error?: PaletteColorOptions;
  //warning?: PaletteColorOptions;
  //info?: PaletteColorOptions;
  //success?: PaletteColorOptions;
  //mode?: PaletteMode;
  //tonalOffset?: PaletteTonalOffset;
  //contrastThreshold?: number;
  //common?: Partial<CommonColors>;
  //grey?: ColorPartial;
  //text?: Partial<TypeText>;
  //divider?: string;
  //action?: Partial<TypeAction>;
  //background?: Partial<TypeBackground>;
};
