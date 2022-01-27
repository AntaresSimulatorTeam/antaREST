import debug from 'debug';
import clsx from 'clsx';
import React, { useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
  Button,
  Chip,
  Tooltip,
  useTheme,
  MenuItem,
  Menu,
} from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import _ from 'lodash';
import { AppState } from '../../App/reducers';
import {
  FileStudyTreeConfigDTO,
  RoleType,
  StudyDownloadDTO,
  StudyMetadata,
  StudyOutput,
} from '../../common/types';
import {
  deleteStudy as callDeleteStudy,
  archiveStudy as callArchiveStudy,
  unarchiveStudy as callUnarchiveStudy,
  renameStudy as callRenameStudy,
  exportStudy,
  exportOuput as callExportOutput,
  getStudyOutputs,
  getStudySynthesis,
  getDownloadOutput,
} from '../../services/api/study';
import { removeStudies } from '../../ducks/study';
import { hasAuthorization, getStudyExtendedName, convertUTCToLocalTime } from '../../services/utils';
import ConfirmationModal from '../ui/ConfirmationModal';
import PermissionModal from './PermissionModal';
import ButtonLoader from '../ui/ButtonLoader';
import RenameModal from './RenameModal';
import { CopyIcon } from '../Data/utils';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import LauncherModal from '../ui/LauncherModal';
import ExportFilterModal from './ExportFilterModal';

const logError = debug('antares:singlestudyview:error');

const buttonStyle = (theme: Theme, color: string) => ({
  width: '120px',
  border: `2px solid ${color}`,
  color,
  margin: theme.spacing(0.5),
  '&:hover': {
    color: 'white',
    backgroundColor: color,
  },
});
const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      flex: '0 0 30%',
      minWidth: '320px',
      minHeight: '250px',
      height: '95%',
      backgroundColor: 'white',
      paddingBottom: theme.spacing(1),
      margin: theme.spacing(1),
      overflow: 'hidden',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
    },
    header: {
      width: '100%',
      flex: '0 0 40px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    container: {
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      boxSizing: 'border-box',
    },
    scrollInfoContainer: {
      marginBottom: theme.spacing(1),
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      boxSizing: 'border-box',
      overflowX: 'hidden',
      overflowY: 'scroll',
    },
    info: {
      width: '90%',
      marginBottom: theme.spacing(0.7),
      color: theme.palette.primary.main,
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      boxSizing: 'border-box',
    },
    alignBaseline: {
      alignItems: 'baseline',
    },
    mainInfo: {
      width: '90%',
      color: theme.palette.primary.main,
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
    },
    studyName: {
      fontSize: '1.3em',
      fontWeight: 'bold',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      marginRight: theme.spacing(1),
    },
    infoTitleContainer: {
      marginBottom: theme.spacing(1),
    },
    infoTitle: {
      marginRight: theme.spacing(1),
      textDecoration: 'underline',
    },
    infoLabel: {
      marginRight: theme.spacing(1),
      fontWeight: 'bold',
    },
    iconLabel: {
      marginRight: theme.spacing(1),
      width: '20px',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'center',
    },
    groupList: {
      flex: 1,
      display: 'flex',
      height: '100%',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
      flexWrap: 'wrap',
      '& > *': {
        margin: theme.spacing(0.5),
      },
    },
    managed: {
      backgroundColor: theme.palette.secondary.main,
    },
    workspace: {
      marginLeft: theme.spacing(1),
    },
    workspaceBadge: {
      border: `1px solid ${theme.palette.primary.main}`,
      borderRadius: '4px',
      padding: '0 4px',
      fontSize: '0.8em',
    },
    buttonContainer: {
      flex: '1 0 100px',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      boxSizing: 'border-box',
      padding: theme.spacing(1),
    },
    deleteContainer: {
      flex: '0 0 30px',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-end',
      alignItems: 'flex-end',
      boxSizing: 'border-box',
    },
    archivingButton: { ...buttonStyle(theme, theme.palette.primary.light), boxSizing: 'border-box' },
    launchButton: { ...buttonStyle(theme, theme.palette.primary.main), boxSizing: 'border-box' },
    exportButton: { ...buttonStyle(theme, theme.palette.primary.main), boxSizing: 'border-box' },
    deleteButton: {
      color: theme.palette.error.main,
      padding: theme.spacing(0),
      marginRight: theme.spacing(2),
      fontSize: '0.8em',
      '&:hover': {
        backgroundColor: '#0000',
      },
    },
    editIcon: {
      '&:hover': {
        color: theme.palette.secondary.main,
        cursor: 'pointer',
      },
    },
  }));

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = {
  removeStudy: (sid: string) => removeStudies([sid]),
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  study: StudyMetadata;
}
type PropTypes = PropsFromRedux & OwnProps;

const InformationView = (props: PropTypes) => {
  const { study, removeStudy, user } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();
  const [studyToLaunch, setStudyToLaunch] = useState<StudyMetadata|undefined>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [openPermissionModal, setOpenPermissionModal] = useState<boolean>(false);
  const [openRenameModal, setOpenRenameModal] = useState<boolean>(false);
  const [openFilterModal, setOpenFilterModal] = useState<boolean>(false);
  const [currentOutput, setCurrentOutput] = useState<string>('');
  const [outputList, setOutputList] = useState<Array<string>>();
  const [outputExportButtonAnchor, setOutputExportButtonAnchor] = React.useState<null | HTMLElement>(null);
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [synthesis, setStudySynthesis] = useState<FileStudyTreeConfigDTO>();

  const openStudyLauncher = (): void => {
    if (study) {
      setStudyToLaunch(study);
    }
  };

  const archiveStudy = async () => {
    try {
      await callArchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:archivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const unarchiveStudy = async () => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:unarchivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const deleteStudy = async () => {
    if (study) {
      // eslint-disable-next-line no-alert
      try {
        await callDeleteStudy(study.id);
        removeStudy(study.id);
        history.push('/');
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtodeletestudy'), e as AxiosError);
        logError('Failed to delete study', study, e);
      }
      setOpenConfirmationModal(false);
    }
  };

  const renameStudy = async (name: string) => {
    if (study) {
      try {
        await callRenameStudy(study.id, name);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtodeletestudy'), e as AxiosError);
        logError('Failed to delete study', study, e);
      }
    }
  };

  const exportOutput = _.debounce(async (output: string) => {
    setOutputExportButtonAnchor(null);
    if (study) {
      try {
        await callExportOutput(study.id, output);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failedToExportOutput'), e as AxiosError);
      }
    }
  }, 2000, { leading: true, trailing: false });

  const onFilter = async (output: string, filter: StudyDownloadDTO): Promise<void> => {
    console.log(filter);
    if (study) {
      try {
        await getDownloadOutput(study.id, output);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failedToExportOutput'), e as AxiosError);
      }
    }
    setOpenFilterModal(false);
  };

  const onExport = (output: string): void => {
    console.log(output);
    setOpenFilterModal(false);
    exportOutput(output);
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleExportFilter = (output: string): void => {
    setCurrentOutput(output);
    setOpenFilterModal(true);
  };

  useEffect(() => {
    (async () => {
      try {
        const res = await getStudyOutputs(study.id);
        setOutputList(res.map((o: StudyOutput) => o.name));
      } catch (e) {
        logError(t('singlestudy:failedToListOutputs'), study, e);
      }
    })();

    (async () => {
      try {
        const res = await getStudySynthesis(study.id);
        setStudySynthesis(res);
      } catch (e) {
        logError(t('singlestudy:failedToListOutputs'), study, e);
      }
    })();
  }, [study, t, enqueueSnackbar]);

  const copyId = (studyId: string): void => {
    try {
      navigator.clipboard.writeText(studyId);
      enqueueSnackbar(t('singlestudy:onStudyIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onStudyIdCopyError'), e as AxiosError);
    }
  };

  return study ? (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:informations')}</Typography>
      </div>
      <div className={classes.container} style={{ height: 'calc(100% - 40px)' }}>
        <div
          className={classes.container}
          style={{ marginTop: theme.spacing(2), marginBottom: theme.spacing(3) }}
        >
          <div className={classes.mainInfo}>
            <Tooltip title={getStudyExtendedName(study)}>
              <Typography className={classes.studyName}>{study.name}</Typography>
            </Tooltip>
            {hasAuthorization(user, study, RoleType.WRITER) && (
              <FontAwesomeIcon
                icon="edit"
                className={classes.editIcon}
                onClick={() => setOpenRenameModal(true)}
              />
            )}
            <div className={classes.workspace}>
              <div className={clsx(classes.workspaceBadge, study.managed ? classes.managed : {})}>
                {study.workspace}
              </div>
            </div>
          </div>
          <div className={classes.mainInfo}>
            <Typography style={{ fontSize: '0.9em', color: 'gray' }}>{study.id}</Typography>
            <Tooltip title={t('singlestudy:copyId') as string} placement="top">
              <CopyIcon style={{ marginLeft: '0.5em', cursor: 'pointer' }} onClick={() => copyId(study.id)} />
            </Tooltip>
          </div>
        </div>
        <div className={classes.scrollInfoContainer}>
          <div
            className={classes.container}
            style={{ flex: 'none', marginBottom: theme.spacing(3) }}
          >
            <div className={clsx(classes.info, classes.infoTitleContainer)}>
              <Typography className={classes.infoTitle}>{t('singlestudy:generalInfo')}</Typography>
            </div>
            <div className={clsx(classes.info, classes.alignBaseline)}>
              <Typography className={classes.infoLabel}>{t('singlestudy:creationDate')}</Typography>
              <Typography variant="body2">
                {convertUTCToLocalTime(study.creationDate)}
              </Typography>
            </div>
            <div className={clsx(classes.info, classes.alignBaseline)}>
              <Typography className={classes.infoLabel}>
                {t('singlestudy:modificationDate')}
              </Typography>
              <Typography variant="body2">
                {convertUTCToLocalTime(study.modificationDate)}
              </Typography>
            </div>
            <div className={clsx(classes.info, classes.alignBaseline)}>
              <Typography className={classes.infoLabel}>{t('singlestudy:version')}</Typography>
              <Typography variant="body2">{study.version}</Typography>
            </div>
          </div>
          <div className={classes.container} style={{ flex: 'none' }}>
            <div className={clsx(classes.info, classes.infoTitleContainer)}>
              <Typography className={classes.infoTitle}>{t('singlestudy:permission')}</Typography>
              {hasAuthorization(user, study, RoleType.ADMIN) && (
                <FontAwesomeIcon
                  icon="edit"
                  className={classes.editIcon}
                  onClick={() => setOpenPermissionModal(true)}
                />
              )}
            </div>
            <div className={classes.info}>
              <div className={classes.iconLabel}>
                <FontAwesomeIcon icon="user" />
              </div>
              <Typography>{study.owner.name}</Typography>
            </div>
            <div className={classes.info}>
              <div className={classes.iconLabel}>
                <FontAwesomeIcon icon="shield-alt" />
              </div>
              <Typography>
                {t(`singlestudy:${(study.publicMode as string).toLowerCase()}PublicModeText`)}
              </Typography>
            </div>
            {study.groups.length > 0 && (
              <div className={classes.info} style={{ alignItems: 'flex-start' }}>
                <div
                  className={classes.info}
                  style={{ width: 'auto', minHeight: '38px', paddingRight: theme.spacing(1) }}
                >
                  <div className={classes.iconLabel}>
                    <FontAwesomeIcon icon="users" />
                  </div>
                  <Typography>{t('singlestudy:groupsLabel')}</Typography>
                </div>
                <div className={classes.groupList}>
                  {study.groups.map((item) => (
                    <Chip key={item.id} label={item.name} color="primary" />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        <div className={classes.buttonContainer}>
          {study.archived ? (
            <ButtonLoader className={classes.archivingButton} onClick={unarchiveStudy}>
              {t('studymanager:unarchive')}
            </ButtonLoader>
          ) : (
            <>
              <Button className={classes.launchButton} onClick={openStudyLauncher}>
                {t('main:launch')}
              </Button>
              <Button
                aria-controls="export-menu"
                aria-haspopup="true"
                className={classes.exportButton}
                onClick={handleClick}
              >
                {t('main:export')}
              </Button>
              <Menu
                id="export-menu"
                anchorEl={anchorEl}
                keepMounted
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem onClick={() => { exportStudy(study.id, false); handleClose(); }}>{t('studymanager:exportWith')}</MenuItem>
                <MenuItem onClick={() => { exportStudy(study.id, true); handleClose(); }}>{t('studymanager:exportWithout')}</MenuItem>
              </Menu>
              {!!outputList && (
                <>
                  <Button className={classes.exportButton} aria-haspopup="true" onClick={(event) => setOutputExportButtonAnchor(event.currentTarget)}>
                    {t('singlestudy:exportOutput')}
                  </Button>
                  <Menu
                    id="simple-menu"
                    anchorEl={outputExportButtonAnchor}
                    keepMounted
                    open={Boolean(outputExportButtonAnchor)}
                    onClose={() => setOutputExportButtonAnchor(null)}
                  >
                    {outputList.map((output) => (
                      <MenuItem onClick={() => handleExportFilter(output)}>
                        {output}
                      </MenuItem>
                    ))}
                  </Menu>
                  <ExportFilterModal open={openFilterModal} synthesis={synthesis} output={currentOutput} onExport={onExport} onFilter={onFilter} onClose={() => setOpenFilterModal(false)} />
                </>
              )}
              {study.managed && (
              <ButtonLoader className={classes.archivingButton} onClick={archiveStudy}>
                {t('studymanager:archive')}
              </ButtonLoader>
              )}
            </>
          )}
        </div>
        <div className={classes.deleteContainer}>
          {study.managed && (
          <Button className={classes.deleteButton} onClick={() => setOpenConfirmationModal(true)}>
            {t('main:delete')}
          </Button>
          )}
        </div>
      </div>
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('studymanager:confirmdelete')}
          handleYes={deleteStudy}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
      {openPermissionModal && study && user && (
        <PermissionModal
          studyId={study.id}
          owner={study.owner}
          groups={study.groups}
          publicMode={study.publicMode}
          name={study.name}
          open={openPermissionModal}
          onClose={() => setOpenPermissionModal(false)}
        />
      )}
      {openRenameModal && (
        <RenameModal
          defaultName={study.name}
          onNewName={(newName) => renameStudy(newName)}
          open={openRenameModal}
          onClose={() => setOpenRenameModal(false)}
        />
      )}
      <LauncherModal open={!!studyToLaunch} study={studyToLaunch} close={() => { setStudyToLaunch(undefined); }} />
    </Paper>
  ) : null;
};

export default connector(InformationView);
