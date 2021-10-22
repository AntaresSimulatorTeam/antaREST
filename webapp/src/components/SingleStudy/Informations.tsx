import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import InformationView from './InformationView';
import TaskView from './TaskView';
import NoteView from './NoteView';
import { LaunchJob, StudyMetadata } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    boxSizing: 'border-box',
    padding: theme.spacing(1),
    overflow: 'auto',
  },
  otherInfo: {
    flex: 1,
    height: '100%',
    minWidth: '350px',
    minHeight: '250px',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    margin: theme.spacing(1),
    paddingBottom: theme.spacing(1),
  }
}));

interface PropTypes {
    study: StudyMetadata;
    jobs: LaunchJob[];
}

const Informations = (props: PropTypes) => {
  const { study, jobs } = props;
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <InformationView study={study} />
      <div className={classes.otherInfo}>
        <TaskView jobs={jobs} />
        <NoteView />
      </div>
    </div>
  );
};

export default Informations;
