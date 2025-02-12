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

import { Box, Typography } from "@mui/material";

function GlobalPageLoadingError() {
  return (
    <Box display="flex" height="100vh">
      <Box flexGrow={1} display="flex" alignItems="center" justifyContent="center" zIndex={999}>
        <Box display="flex" justifyContent="center" alignItems="center" flexDirection="column">
          <Box
            display="flex"
            width="100%"
            justifyContent="center"
            alignItems="center"
            flexDirection="column"
            flexWrap="nowrap"
            boxSizing="border-box"
          >
            <Typography variant="h4" component="h4" color="primary" my={2}>
              Oops, an unexpected error happened.
              <br />
              Please try to refresh the page.
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default GlobalPageLoadingError;
