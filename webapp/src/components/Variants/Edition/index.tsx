import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { DropResult } from 'react-beautiful-dnd';
import QueueIcon from '@material-ui/icons/Queue';
import CloudDownloadOutlinedIcon from '@material-ui/icons/CloudDownloadOutlined';
import { CommandItem, JsonCommandItem } from './CommandTypes';
import CommandListView from './DraggableCommands/CommandListView';
import { reorder, fromCommandDTOToCommandItem, fromCommandDTOToJsonCommand, exportJson } from './utils';
import { appendCommand, deleteCommand, getCommand, getCommands, moveCommand, updateCommand, replaceCommands } from '../../../services/api/variant';
import AddCommandModal from './AddCommandModal';
import { CommandDTO } from '../../../common/types';
import CommandImportButton from './DraggableCommands/CommandImportButton';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: 1,
    height: '98%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflowY: 'hidden',
  },
  header: {
    width: '100%',
    height: '80px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  body: {
    width: '100%',
    maxHeight: '90%',
    minHeight: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflow: 'auto',
    boxSizing: 'border-box',
  },
  addButton: {
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  headerIcon: {
    width: '24px',
    height: 'auto',
    cursor: 'pointer',
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 3),
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
}));

interface PropTypes {
    studyId: string;
}

const EditionView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { studyId } = props;
  const [openAddCommandModal, setOpenAddCommandModal] = useState<boolean>(false);
  const [commands, setCommands] = useState<Array<CommandItem>>([]);

  const onDragEnd = async ({ destination, source }: DropResult) => {
    // dropped outside the list
    if (!destination) return;
    const oldCommands = commands.concat([]);
    try {
      const elm = commands[source.index];
      const newItems = reorder(commands, source.index, destination.index);
      setCommands(newItems);
      await moveCommand(studyId, (elm.id as string), destination.index);
      enqueueSnackbar(t('variants:moveSuccess'), { variant: 'success' });
    } catch (e) {
      setCommands(oldCommands);
      enqueueSnackbar(t('variants:moveError'), { variant: 'error' });
    }
  };

  const onSave = async (index: number) => {
    try {
      const elm = commands[index];
      if (elm.updated) {
        await updateCommand(studyId, (elm.id as string), elm);
        let tmpCommand: Array<CommandItem> = [];
        tmpCommand = tmpCommand.concat(commands);
        tmpCommand[index].updated = false;
        setCommands(tmpCommand);
        enqueueSnackbar(t('variants:saveSuccess'), { variant: 'success' });
      }
    } catch (e) {
      enqueueSnackbar(t('variants:saveError'), { variant: 'error' });
    }
  };

  const onDelete = async (index: number) => {
    try {
      const elm = commands[index];
      await deleteCommand(studyId, (elm.id as string));
      setCommands((commandList) => commandList.filter((item, idx) => idx !== index));
      enqueueSnackbar(t('variants:deleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:deleteError'), { variant: 'error' });
    }
  };

  const onNewCommand = async (action: string) => {
    try {
      const elmDTO: CommandDTO = { action, args: {} };
      const newId = await appendCommand(studyId, elmDTO);
      setCommands(commands.concat([{ ...elmDTO, id: newId, updated: false }]));
      enqueueSnackbar(t('variants:addSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:addError'), { variant: 'error' });
    }
  };

  const onArgsUpdate = (index: number, args: object) => {
    let tmpCommand: Array<CommandItem> = [];
    tmpCommand = tmpCommand.concat(commands);
    tmpCommand[index].args = { ...args };
    tmpCommand[index].updated = true;
    setCommands(tmpCommand);
  };

  const onCommandImport = async (index: number, json: object) => {
    try {
      let tmpCommand: Array<CommandItem> = [];
      tmpCommand = tmpCommand.concat(commands);
      const elm = tmpCommand[index];
      // eslint-disable-next-line dot-notation
      elm.action = (json as any)['action'];
      // eslint-disable-next-line dot-notation
      elm.args = { ...((json as any)['args'] as object) };
      elm.updated = false;
      await updateCommand(studyId, (elm.id as string), elm);
      setCommands(tmpCommand);
      enqueueSnackbar(t('variants:importSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:importError'), { variant: 'error' });
    }
  };

  const onCommandExport = async (index: number) => {
    try {
      const elm = await getCommand(studyId, commands[index].id as string);
      exportJson({ action: elm.action, args: elm.args }, `${elm.id}_command.json`);
    } catch (e) {
      enqueueSnackbar(t('variants:exportError'), { variant: 'error' });
    }
  };

  const onGlobalExport = async () => {
    try {
      const items = await getCommands(studyId);
      exportJson(fromCommandDTOToJsonCommand(items), `${studyId}_commands.json`);
    } catch (e) {
      enqueueSnackbar(t('variants:exportError'), { variant: 'error' });
    }
  };

  const onGlobalImport = async (json: object) => {
    try {
      const globalJson: Array<JsonCommandItem> = (json as Array<JsonCommandItem>);
      await replaceCommands(studyId, globalJson);

      const dtoItems = await getCommands(studyId);
      setCommands(fromCommandDTOToCommandItem(dtoItems));
      enqueueSnackbar(t('variants:importSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:importError'), { variant: 'error' });
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const dtoItems = await getCommands(studyId);
        setCommands(fromCommandDTOToCommandItem(dtoItems));
      } catch (e) {
        enqueueSnackbar(t('variants:fetchCommandError'), { variant: 'error' });
      }
    };
    init();
  }, [enqueueSnackbar, studyId, t]);

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <CommandImportButton onImport={onGlobalImport} />
        <CloudDownloadOutlinedIcon className={classes.headerIcon} onClick={onGlobalExport} />
        <QueueIcon className={classes.headerIcon} onClick={() => setOpenAddCommandModal(true)} />
      </div>
      <div className={classes.body}>
        <CommandListView items={commands} onDragEnd={onDragEnd} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} onCommandImport={onCommandImport} onCommandExport={onCommandExport} />
      </div>
      {openAddCommandModal && (
        <AddCommandModal
          open={openAddCommandModal}
          onClose={() => setOpenAddCommandModal(false)}
          onNewCommand={onNewCommand}
        />
      )}
    </div>
  );
};

export default EditionView;
