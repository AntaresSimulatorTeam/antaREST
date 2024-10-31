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

import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Box, Divider, styled, Tooltip, Typography } from "@mui/material";

import { StudyMetadata, VariantTree } from "@/common/types";
import { PUBLIC_MODE_LIST } from "@/components/common/utils/constants";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  countAllChildrens,
  displayVersionName,
} from "@/services/utils";

const MAX_STUDY_TITLE_LENGTH = 45;

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.text.secondary,
}));

const LinkText = styled(Link)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.secondary.main,
}));

const StyledDivider = styled(Divider)(({ theme }) => ({
  margin: theme.spacing(0, 1),
  width: "1px",
  height: "20px",
  backgroundColor: theme.palette.divider,
}));

const BoxContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  justifyContent: "flex-start",
  alignItems: "center",
  margin: theme.spacing(0, 3),
}));

interface Props {
  study: StudyMetadata | undefined;
  parent: StudyMetadata | undefined;
  childrenTree: VariantTree | undefined;
}

function Details({ study, parent, childrenTree }: Props) {
  const [t, i18n] = useTranslation();
  const publicModeLabel =
    PUBLIC_MODE_LIST.find((mode) => mode.id === study?.publicMode)?.name || "";

  if (!study) {
    return null;
  }

  return (
    <BoxContainer
      sx={{
        my: 1,
        width: 1,
        boxSizing: "border-box",
      }}
    >
      <BoxContainer sx={{ ml: 0 }}>
        <ScheduleOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
      </BoxContainer>
      <BoxContainer>
        <UpdateOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>
          {buildModificationDate(study.modificationDate, t, i18n.language)}
        </TinyText>
      </BoxContainer>
      <StyledDivider />
      <BoxContainer>
        <TinyText>{`v${displayVersionName(study.version)}`}</TinyText>
      </BoxContainer>
      {parent && (
        <BoxContainer>
          <AltRouteOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <Tooltip title={parent.name}>
            <LinkText to={`/studies/${parent.id}`}>
              {`${parent.name.substring(0, MAX_STUDY_TITLE_LENGTH)}...`}
            </LinkText>
          </Tooltip>
        </BoxContainer>
      )}
      {childrenTree && (
        <BoxContainer>
          <AccountTreeOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <TinyText>{countAllChildrens(childrenTree)}</TinyText>
        </BoxContainer>
      )}
      <StyledDivider />
      <BoxContainer>
        <PersonOutlineOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>{study.owner.name}</TinyText>
      </BoxContainer>
      <BoxContainer>
        <SecurityOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>{t(publicModeLabel)}</TinyText>
      </BoxContainer>
    </BoxContainer>
  );
}

export default Details;
