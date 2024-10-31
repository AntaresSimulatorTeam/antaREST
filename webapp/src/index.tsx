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

import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";

import { StyledEngineProvider } from "@mui/material";

import App from "./components/App";
import store from "./redux/store";
import { Config, initConfig } from "./services/config";
import storage, { StorageKey } from "./services/utils/localStorage";

import "./index.css";

initConfig((config: Config) => {
  const versionInstalled = storage.getItem(StorageKey.Version);
  storage.setItem(StorageKey.Version, config.version.gitcommit);
  if (versionInstalled !== config.version.gitcommit) {
    window.location.reload();
  }

  const container = document.getElementById("root") as HTMLElement;
  const root = createRoot(container);

  root.render(
    <StyledEngineProvider injectFirst>
      <Provider store={store}>
        <App />
      </Provider>
    </StyledEngineProvider>,
  );
});
