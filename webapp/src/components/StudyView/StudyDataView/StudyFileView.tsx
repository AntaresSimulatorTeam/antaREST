/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { makeStyles, Theme, createStyles, Paper } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { getStudyData } from '../../../services/api/study';
import ImportForm from './utils/ImportForm';
import { CommonStudyStyle } from './utils/utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  ...CommonStudyStyle(theme),
  code: {
    whiteSpace: 'pre',
  },
}));

interface PropTypes {
  study: string;
  url: string;
  studyData: any;
  setStudyData: (elm: any) => void;
  filterOut: Array<string>;
}

const StudyDataView = (props: PropTypes) => {
  const { study, url, filterOut, studyData, setStudyData } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [data, setData] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const [isEditable, setEditable] = useState<boolean>(true);
  const [formatedPath, setFormatedPath] = useState<string>('');

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      setData(res);
    } catch (e) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  const successImport = () => {
    // this is to refresh the tree / view
    const newData = { ...studyData };
    setStudyData(newData);
    enqueueSnackbar(<Translation>{(t) => t('studymanager:savedatasuccess')}</Translation>, { variant: 'success' });
  };

  useEffect(() => {
    const urlParts = url.split('/');
    const tmpUrl = urlParts.filter((item) => item);
    setFormatedPath(tmpUrl.join('/'));
    if (tmpUrl.length > 0) {
      setEditable(!filterOut.includes(tmpUrl[0]));
    }
    if (urlParts.length < 2) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
      return;
    }
    loadFileData();
  }, [url, filterOut]);

  return (
    <>
      {data && (
      <div className={classes.root}>
        {
           isEditable && (
           <div className={classes.header}>
             <ImportForm study={study} path={formatedPath} callback={successImport} />
           </div>
           )}
        <Paper className={classes.content}>
          <code className={classes.code}>{data}</code>
        </Paper>
      </div>
      )}
      {!loaded && (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
};

export default StudyDataView;
