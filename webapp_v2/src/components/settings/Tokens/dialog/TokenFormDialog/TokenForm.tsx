import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useRef, useState } from "react";
import { Controller, useFieldArray } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { v4 as uuidv4 } from "uuid";
import DeleteIcon from "@mui/icons-material/Delete";
import GroupIcon from "@mui/icons-material/Group";
import { TokenFormDialogProps } from ".";
import { GroupDTO, RoleType } from "../../../../../common/types";
import usePromise from "../../../../../hooks/usePromise";
import { getGroups } from "../../../../../services/api/user";
import { roleToString, sortByName } from "../../../../../services/utils";
import { FormObj } from "../../../../common/dialogs/FormDialog";
import { RESERVED_GROUP_NAMES, ROLE_TYPE_KEYS } from "../../../utils";

/**
 * Types
 */

interface Props extends FormObj {
  onlyPermissions: TokenFormDialogProps["onlyPermissions"];
}

/**
 * Component
 */

function TokenForm(props: Props) {
  const {
    control,
    register,
    getValues,
    formState: { errors },
    onlyPermissions,
  } = props;

  const groupLabelId = useRef(uuidv4()).current;
  const { fields, append, remove } = useFieldArray({
    control,
    name: "permissions",
  });
  const [selectedGroup, setSelectedGroup] = useState<GroupDTO>();
  const { data: groups, isLoading: isGroupsLoading } = usePromise(getGroups);
  const { t } = useTranslation();
  const allowToAddPermission =
    selectedGroup &&
    !getValues("permissions").some(
      ({ group }: { group: GroupDTO }) => group.id === selectedGroup.id
    );

  const filteredAndSortedGroups = useMemo(() => {
    if (!groups) {
      return [];
    }
    return sortByName(
      groups.filter((group) => !RESERVED_GROUP_NAMES.includes(group.name))
    );
  }, [groups]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleGroupChange = (event: SelectChangeEvent<string>) => {
    const groupId = event.target.value;
    const group = groups?.find((gp) => gp.id === groupId);
    setSelectedGroup(group);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {/* Name */}
      {!onlyPermissions && (
        <>
          <TextField
            sx={{ mx: 0 }}
            label={t("main:name")}
            error={!!errors.name}
            helperText={errors.name?.message}
            required
            fullWidth
            {...register("name", {
              required: t("main:form.field.required") as string,
            })}
          />
          <FormControlLabel
            control={
              <Checkbox defaultChecked={false} {...register("linkToUser")} />
            }
            label={t("settings:linkTokenLabel")}
          />
        </>
      )}
      {/* Permissions */}
      <Paper
        sx={{
          p: 2,
          mt: 2,
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        }}
      >
        <Typography>{t("settings:permissionsLabel")}</Typography>
        {isGroupsLoading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignContent: "center",
              mt: 2,
            }}
          >
            <CircularProgress color="inherit" />
          </Box>
        )}
        {filteredAndSortedGroups.length > 0 && (
          <>
            <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
              <FormControl sx={{ mr: 2, flex: 1 }} size="small">
                <InputLabel id={groupLabelId}>{t("settings:group")}</InputLabel>
                <Select
                  labelId={groupLabelId}
                  label={t("settings:group")}
                  defaultValue=""
                  onChange={handleGroupChange}
                >
                  {filteredAndSortedGroups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                size="small"
                disabled={!allowToAddPermission}
                onClick={() => {
                  append({ group: selectedGroup, type: RoleType.READER });
                }}
              >
                {t("settings:addButton")}
              </Button>
            </Box>
            <List>
              {fields.map((field, index) => (
                <ListItem
                  key={field.id}
                  secondaryAction={
                    <>
                      <Controller
                        control={control}
                        name={`permissions.${index}.type`}
                        render={({ field }) => (
                          <Select variant="standard" {...field}>
                            {ROLE_TYPE_KEYS.map((key) => (
                              <MenuItem key={key} value={RoleType[key]}>
                                {roleToString(RoleType[key])}
                              </MenuItem>
                            ))}
                          </Select>
                        )}
                      />
                      <IconButton edge="end" onClick={() => remove(index)}>
                        <DeleteIcon />
                      </IconButton>
                    </>
                  }
                  disablePadding
                  dense
                >
                  <ListItemButton
                    sx={{ cursor: "default" }}
                    disableRipple
                    disableGutters
                  >
                    <ListItemIcon sx={{ minWidth: 0, p: "0 15px 0 5px" }}>
                      <GroupIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={getValues(`permissions.${index}.group.name`)}
                      title={getValues(`permissions.${index}.group.name`)}
                      sx={{
                        ".MuiTypography-root": {
                          textOverflow: "ellipsis",
                          overflow: "hidden",
                          maxWidth: "325px",
                          whiteSpace: "nowrap",
                        },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </>
        )}
      </Paper>
    </>
  );
}

export default TokenForm;
