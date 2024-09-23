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

import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Avatar from "@mui/material/Avatar";
import { Icon } from "@mui/material";
import { SvgIconComponent } from "@mui/icons-material";

interface ListItem {
  content: React.ReactNode;
  label: string;
  icon: SvgIconComponent;
  iconColor?: string;
}

interface Props {
  items: ListItem[];
}

function DetailsList({ items }: Props) {
  return (
    <List
      sx={{
        width: 1,
        backgroundColor: "#222333",
      }}
    >
      {items.map((item) => (
        <ListItem key={item.label} sx={{ py: 0 }}>
          <ListItemAvatar>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                backgroundColor: item.iconColor || "default",
              }}
            >
              <Icon
                component={item.icon}
                sx={{
                  width: 20,
                  height: 20,
                }}
              />
            </Avatar>
          </ListItemAvatar>
          <ListItemText primary={item.content} secondary={item.label} />
        </ListItem>
      ))}
    </List>
  );
}

export default DetailsList;
