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

import { configureStore } from "@reduxjs/toolkit";
import type { ThunkAction } from "redux-thunk";
import type { AnyAction } from "redux";
import rootReducer, { type AppState } from "./ducks";
import localStorageMiddleware from "./middlewares/localStorageMiddleware";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoreActions: true,
      },
    }).prepend(localStorageMiddleware.middleware),
});

export type AppStore = typeof store;

export type AppDispatch = typeof store.dispatch;

export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  AppState,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  any, // TODO: issue with unknown
  AnyAction
>;

export interface AppAsyncThunkConfig {
  state: AppState;
  dispatch: AppDispatch;
}

export default store;
