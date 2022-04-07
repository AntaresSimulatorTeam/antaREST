import React, { useState, useEffect } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  Box,
  Divider,
  Typography,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import SaveIcon from '@material-ui/icons/Save';
import VisibilityIcon from '@material-ui/icons/Visibility';
import DeleteIcon from '@material-ui/icons/Delete';
import HeightIcon from '@material-ui/icons/Height';
import ConfirmationModal from '../../ui/ConfirmationModal';
import { XpansionCandidate } from './types';
import { LinkCreationInfo } from '../MapView/types';
import SelectBasic from '../../ui/SelectBasic';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-end',
    },
    title: {
      color: theme.palette.primary.main,
      fontSize: '1.25rem',
      fontWeight: 400,
      lineHeight: 1.334,
    },
    fields: {
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'center',
      width: '100%',
      flexWrap: 'wrap',
      marginBottom: theme.spacing(2),
      '&> div': {
        width: '270px',
        marginRight: theme.spacing(2),
      },
    },
    selectBox: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-start',
      width: '100%',
      marginBottom: theme.spacing(2),
      '&> div': {
        marginRight: theme.spacing(2),
        marginBottom: theme.spacing(2),
      },
    },
    select: {
      display: 'flex',
      alignItems: 'center',
      width: '270px',
    },
    deleteIcon: {
      cursor: 'pointer',
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    buttons: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    divider: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
    },
    formControl: {
      minWidth: '130px',
    },
    alreadyInstalled: {
      minWidth: '250px',
    },
    icon: {
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      '&:hover': {
        color: theme.palette.secondary.main,
        cursor: 'pointer',
      },
    },
    saveButton: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      height: '30px',
      marginRight: theme.spacing(1),
    },
    buttonElement: {
      margin: theme.spacing(0.2),
    },
    inputPack: {
      backgroundColor: 'rgba(0, 0, 0, 0.09)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: 'unset !important',
      maxWidth: '556px !important',
      height: '80px',
      paddingLeft: theme.spacing(2),
      paddingRight: theme.spacing(2),
      borderRadius: '5px',
      '&> div': {
        width: '270px',
      },
      '&> div > div': {
        backgroundColor: '#e8e8e8',
        '&:hover': {
          backgroundColor: '#dedede',
        },
        '&:focused': {
          backgroundColor: '#e8e8e8',
        },
      },
    },
    marginR: {
      marginRight: theme.spacing(2),
    },
    arrowIcon: {
      transform: 'rotate(90deg)',
      marginRight: theme.spacing(2),
    },
  }));

interface PropType {
    candidate: XpansionCandidate;
    links: Array<LinkCreationInfo>;
    capacities: Array<string>;
    deleteCandidate: (name: string) => Promise<void>;
    updateCandidate: (name: string, value: XpansionCandidate) => Promise<void>;
    onRead: (filename: string) => Promise<void>;
}

const CandidateForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { candidate, links, capacities, deleteCandidate, updateCandidate, onRead } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [currentCandidate, setCurrentCandidate] = useState<XpansionCandidate>(candidate);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);

  const tabLinks = links.map((item) => `${item.area1} - ${item.area2}`);

  const handleChange = (key: string, value: string | number) => {
    setSaveAllowed(true);
    setCurrentCandidate({ ...currentCandidate, [key]: value });
  };

  useEffect(() => {
    if (candidate) {
      setCurrentCandidate(candidate);
      setSaveAllowed(false);
    }
  }, [candidate]);

  return (
    <Box>
      <Box>
        <Box className={classes.header}>
          <Typography className={classes.title}>
            {t('main:general')}
          </Typography>
          <Box className={classes.buttons}>
            <Button
              variant="outlined"
              color="primary"
              className={classes.saveButton}
              style={{ border: '2px solid' }}
              onClick={() => { updateCandidate(currentCandidate.name, currentCandidate); setSaveAllowed(false); }}
              disabled={!saveAllowed}
            >
              <SaveIcon className={classes.buttonElement} style={{ width: '16px', height: '16px' }} />
              <Typography className={classes.buttonElement} style={{ fontSize: '12px' }}>{t('main:save')}</Typography>
            </Button>
            <DeleteIcon className={classes.deleteIcon} onClick={() => setOpenConfirmationModal(true)} />
          </Box>
        </Box>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField label={t('main:name')} variant="filled" value={currentCandidate.name} onChange={(e) => handleChange('name', e.target.value)} />
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:link')} label="link" items={tabLinks} value={currentCandidate.link} handleChange={handleChange} />
          </Box>
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          {t('main:settings')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField type="number" label={t('xpansion:annualCost')} variant="filled" value={currentCandidate['annual-cost-per-mw'] || ''} onChange={(e) => handleChange('annual-cost-per-mw', parseFloat(e.target.value))} />
        </Box>
        <Box className={classes.fields}>
          <Box className={classes.inputPack}>
            <TextField className={classes.marginR} type="number" label={t('xpansion:unitSize')} variant="filled" value={currentCandidate['unit-size'] || ''} onChange={(e) => handleChange('unit-size', parseFloat(e.target.value))} />
            <TextField type="number" label={t('xpansion:maxUnits')} variant="filled" value={currentCandidate['max-units'] || ''} onChange={(e) => handleChange('max-units', parseFloat(e.target.value))} />
          </Box>
          <HeightIcon className={classes.arrowIcon} color="primary" />
          {/* <Typography className={classes.marginR} variant="body1" component="p">ou</Typography> */}
          <Box className={classes.inputPack}>
            <TextField type="number" label={t('xpansion:maxInvestments')} variant="filled" value={currentCandidate['max-investment'] || ''} onChange={(e) => handleChange('max-investment', parseFloat(e.target.value))} />
          </Box>
        </Box>
        <Box className={classes.fields}>
          <TextField type="number" label={t('xpansion:alreadyICapacity')} variant="filled" value={currentCandidate['already-installed-capacity'] || ''} onChange={(e) => handleChange('already-installed-capacity', parseFloat(e.target.value))} />
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          {t('xpansion:timeSeries')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.selectBox}>
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:linkProfile')} label="link-profile" items={capacities} value={currentCandidate['link-profile'] || ''} handleChange={handleChange} optional />
            <VisibilityIcon className={classes.icon} color="primary" onClick={() => currentCandidate['link-profile'] && onRead(currentCandidate['link-profile'] || '')} />
          </Box>
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:alreadyILinkProfile')} label="already-installed-link-profile" items={capacities} value={currentCandidate['already-installed-link-profile'] || ''} handleChange={handleChange} optional />
            <VisibilityIcon className={classes.icon} color="primary" onClick={() => currentCandidate['already-installed-link-profile'] && onRead(currentCandidate['already-installed-link-profile'] || '')} />
          </Box>
        </Box>
      </Box>
      {openConfirmationModal && candidate && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message="Êtes-vous sûr de vouloir supprimer ce candidat?"
          handleYes={() => { deleteCandidate(currentCandidate.name); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </Box>
  );
};

export default CandidateForm;
