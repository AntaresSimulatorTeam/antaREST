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

import { useState } from "react";
import { useTranslation } from "react-i18next";

import TokenIcon from "@mui/icons-material/Token";
import { Box, Button } from "@mui/material";

import { BotDTO } from "@/common/types";
import SearchFE from "@/components/common/fieldEditors/SearchFE";

import CreateTokenDialog from "./dialog/CreateTokenDialog";

interface Props {
  setSearchValue: (v: string) => void;
  addToken: (user: BotDTO) => void;
  reloadFetchTokens: () => void;
}

function Header(props: Props) {
  const { setSearchValue, addToken, reloadFetchTokens } = props;
  const { t } = useTranslation();
  const [showCreateTokenModal, setShowCreateTokenModal] = useState(false);

  return (
    <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: "5px",
        }}
      >
        <SearchFE sx={{ m: 0 }} onSearchValueChange={setSearchValue} />
        <Button
          startIcon={<TokenIcon />}
          variant="outlined"
          onClick={() => setShowCreateTokenModal(true)}
        >
          {t("global.create")}
        </Button>
      </Box>
      {showCreateTokenModal && (
        <CreateTokenDialog
          open
          addToken={addToken}
          reloadFetchTokens={reloadFetchTokens}
          closeDialog={() => setShowCreateTokenModal(false)}
        />
      )}
    </>
  );
}

export default Header;
