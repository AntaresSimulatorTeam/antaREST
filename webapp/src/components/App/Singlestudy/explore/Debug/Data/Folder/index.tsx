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
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Menu,
  MenuItem,
} from "@mui/material";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import DeleteIcon from "@mui/icons-material/Delete";
import {
  getFileIcon,
  getFileType,
  type TreeFolder,
  type DataCompProps,
  isFolder,
  canEditFile,
} from "../../utils.ts";
import { Fragment, useState } from "react";
import EmptyView from "../../../../../../common/page/EmptyView.tsx";
import { useTranslation } from "react-i18next";
import { Filename, Menubar } from "../styles.tsx";
import UploadFileButton from "../../../../../../common/buttons/UploadFileButton.tsx";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog.tsx";
import useConfirm from "../../../../../../../hooks/useConfirm.ts";
import { deleteFile } from "../../../../../../../services/api/studies/raw";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar.tsx";
import { toError } from "../../../../../../../utils/fnUtils.ts";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../../common/types.ts";
import CreateFoldersDialog from "@/components/App/Singlestudy/explore/Debug/Data/Folder/CreateFoldersDialog.tsx";

const FolderIcon = getFileIcon("folder");

function Folder({
  filename,
  filePath,
  treeData,
  canEdit,
  setSelectedFile,
  reloadTreeData,
  studyId,
}: DataCompProps) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const replaceAction = useConfirm();
  const deleteAction = useConfirm();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const [menuData, setMenuData] = useState<null | {
    anchorEl: HTMLElement;
    filePath: string;
    isFolder: boolean;
  }>(null);

  const [displayNewFolderModal, setDisplayNewFolderModal] = useState(false);

  const treeFolder = treeData as TreeFolder;
  const fileList = Object.entries(treeFolder);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleValidateUpload = (file: File) => {
    const childWithSameName = treeFolder[file.name];
    if (childWithSameName) {
      if (isFolder(childWithSameName)) {
        throw new Error(t("study.debug.folder.upload.error.replaceFolder"));
      }

      return replaceAction.showConfirm();
    }
  };

  const handleMenuClose = () => {
    setMenuData(null);
  };

  const handleCreateFolderClick = () => {
    setDisplayNewFolderModal(true);
  };

  const handleDeleteClick = () => {
    handleMenuClose();

    if (!menuData) {
      return;
    }

    deleteAction.showConfirm().then((confirm) => {
      if (confirm) {
        deleteFile({ studyId, path: menuData.filePath })
          .then(() => {
            reloadTreeData();
          })
          .catch((err) => {
            enqueueErrorSnackbar("Delete failed", toError(err));
          });
      }
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <List
        subheader={
          <ListSubheader>
            <Menubar>
              <Filename>{filename}</Filename>
              {canEdit && (
                <>
                  <Button variant="contained" size="small" onClick={handleCreateFolderClick}>
                    New Folder
                  </Button>
                  <UploadFileButton
                    studyId={studyId}
                    path={(file) => `${filePath}/${file.name}`}
                    onUploadSuccessful={reloadTreeData}
                    validate={handleValidateUpload}
                  />
                </>
              )}
            </Menubar>
          </ListSubheader>
        }
        sx={{
          height: 1,
          overflow: "auto",
          // Prevent scroll to display
          ...(fileList.length === 0 && {
            display: "flex",
            flexDirection: "column",
          }),
        }}
        dense
      >
        {fileList.length > 0 ? (
          fileList.map(([filename, data], index, arr) => {
            const path = `${filePath}/${filename}`;
            const type = getFileType(data);
            const Icon = getFileIcon(type);
            const isNotLast = index !== arr.length - 1;

            return (
              <Fragment key={filename}>
                <ListItem
                  secondaryAction={
                    canEditFile(study, path) && (
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={(event) => {
                          setMenuData({
                            anchorEl: event.currentTarget,
                            filePath: path,
                            isFolder: type === "folder",
                          });
                        }}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    )
                  }
                  disablePadding
                >
                  <ListItemButton
                    onClick={() =>
                      setSelectedFile({
                        filename,
                        fileType: type,
                        filePath: path,
                        treeData: data,
                      })
                    }
                  >
                    <ListItemIcon>
                      <Icon />
                    </ListItemIcon>
                    <ListItemText
                      title={filename}
                      primary={filename}
                      primaryTypographyProps={{
                        sx: { overflow: "hidden", textOverflow: "ellipsis" },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
                {isNotLast && <Divider variant="fullWidth" />}
              </Fragment>
            );
          })
        ) : (
          <EmptyView title={t("study.debug.folder.empty")} icon={FolderIcon} />
        )}
      </List>
      {/* Items menu */}
      <Menu anchorEl={menuData?.anchorEl} open={!!menuData} onClose={handleMenuClose}>
        <MenuItem onClick={handleDeleteClick}>
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          {t("global.delete")}
        </MenuItem>
      </Menu>
      <CreateFoldersDialog
        open={displayNewFolderModal}
        onCancel={() => setDisplayNewFolderModal(false)}
        studyId={studyId}
        parentPath={filePath}
        reloadTreeData={reloadTreeData}
      />
      {/* Confirm file replacement */}
      <ConfirmationDialog
        title={t("study.debug.folder.upload.replaceFileConfirm.title")}
        confirmButtonText={t("global.replace")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={replaceAction.isPending}
        onConfirm={replaceAction.yes}
        onCancel={replaceAction.no}
      >
        {t("study.debug.folder.upload.replaceFileConfirm.message")}
      </ConfirmationDialog>
      {/* Confirm file deletion */}
      <ConfirmationDialog
        title={t("study.debug.file.deleteConfirm.title")}
        titleIcon={DeleteIcon}
        confirmButtonText={t("global.delete")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={deleteAction.isPending}
        onConfirm={deleteAction.yes}
        onCancel={deleteAction.no}
      >
        {t("study.debug.file.deleteConfirm.message")}
      </ConfirmationDialog>
    </>
  );
}

export default Folder;
