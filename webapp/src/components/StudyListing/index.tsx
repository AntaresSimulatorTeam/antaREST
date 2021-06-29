import React from 'react';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import StudyBlockSummaryView from './StudyBlockSummaryView';
import StudyListSummaryView from './StudyListSummaryView';
import { StudyMetadata } from '../../common/types';
import { removeStudies } from '../../ducks/study';
import { deleteStudy as callDeleteStudy, launchStudy as callLaunchStudy } from '../../services/api/study';

const logError = debug('antares:studyblockview:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    overflow: 'auto',
  },
  containerGrid: {
    display: 'flex',
    width: '100%',
    flexWrap: 'wrap',
    paddingTop: theme.spacing(2),
    justifyContent: 'space-around',
  },
  containerList: {
    display: 'flex',
    width: '100%',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    paddingTop: theme.spacing(2),
  },
}));

const mapState = () => ({ /* noop */ });

const mapDispatch = ({
  removeStudy: (sid: string) => removeStudies([sid]),
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  studies: StudyMetadata[];
  isList: boolean;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyListing = (props: PropTypes) => {
  const classes = useStyles();
  const { studies, removeStudy, isList } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();

  const launchStudy = async (study: StudyMetadata) => {
    try {
      await callLaunchStudy(study.id);
      enqueueSnackbar(t('studymanager:studylaunched', { studyname: study.name }), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
      logError('Failed to launch study', study, e);
    }
  };

  const deleteStudy = async (study: StudyMetadata) => {
    // eslint-disable-next-line no-alert
    try {
      await callDeleteStudy(study.id);
      removeStudy(study.id);
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtodeletestudy'), { variant: 'error' });
      logError('Failed to delete study', study, e);
    }
  };

  return (
    <div className={classes.root}>
      <div className={isList ? classes.containerList : classes.containerGrid}>
        {
          studies.map((s) => (isList ? (
            <StudyListSummaryView
              key={s.id}
              study={s}
              launchStudy={launchStudy}
              deleteStudy={deleteStudy}
            />
          ) : (
            <StudyBlockSummaryView
              key={s.id}
              study={s}
              launchStudy={launchStudy}
              deleteStudy={deleteStudy}
            />
          )))
        }
      </div>
    </div>
  );
};

export default connector(StudyListing);
