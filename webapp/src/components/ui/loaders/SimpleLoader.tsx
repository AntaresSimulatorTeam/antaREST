import React from 'react';
import { CircularProgress, createStyles, makeStyles } from '@material-ui/core';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles(() =>
  createStyles({
    rootLoader: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'absolute',
      width: '100%',
      height: '100%',
      zIndex: 999,
    },
    shadow: {
      zIndex: 998,
      opacity: 0.9,
    },
    loaderWheel: {
      width: '98px',
      height: '98px',
    },
    loaderMessage: {
      marginTop: '1em',
    },
    loaderContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexFlow: 'column',
    },
  }));

interface PropTypes {
  progress?: number;
  message?: string;
  color?: string;
}

const SimpleLoader = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { progress, message, color } = props;
  return (
    <>
      <div className={classes.rootLoader}>
        <div className={classes.loaderContainer}>
          {progress === undefined ?
            <CircularProgress className={classes.loaderWheel} /> :
            <CircularProgress variant="determinate" className={classes.loaderWheel} value={progress} />
          }
          {message && <div className={classes.loaderMessage}>{t(message)}</div>}
        </div>
      </div>
      <div className={clsx(classes.rootLoader, classes.shadow)} style={{ backgroundColor: color }} />
    </>
  );
};

SimpleLoader.defaultProps = {
  progress: undefined,
  message: undefined,
  color: '#fff',
};

export default SimpleLoader;
