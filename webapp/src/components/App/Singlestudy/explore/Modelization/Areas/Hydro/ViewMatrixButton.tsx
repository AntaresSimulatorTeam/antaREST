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

import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props {
  label: string;
  onClick: () => void;
}

function ViewMatrixButton({ label, onClick }: Props) {
  const { t } = useTranslation();

  return (
    <Button variant="outlined" size="small" sx={{ mt: 3, mr: 3 }} onClick={onClick}>
      {t(label)}
    </Button>
  );
}

export default ViewMatrixButton;
