import React, { useEffect, useState } from 'react';
import { Graph } from 'react-d3-graph';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
  Button,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { getAreaPositions, getSynthesis } from '../../../services/api/study';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import PanelCardView from './PanelCardView';
import { NodeProperties, LinkProperties, StudyProperties, AreasConfig } from './types';
import CreateAreaModal from './CreateAreaModal';
import NodeView from './NodeView';

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
      width: '100%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      boxSizing: 'border-box',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      borderTopLeftRadius: theme.shape.borderRadius,
      borderTopRightRadius: theme.shape.borderRadius,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    autosizer: {
      display: 'block',
      width: '100%',
      height: '100%',
      position: 'relative',
    },
    popup: {
      position: 'absolute',
      right: '30px',
      top: '100px',
      width: '200px',
    },
    button: {
      position: 'absolute',
      left: '10px',
      bottom: '10px',
      ...buttonStyle(theme, theme.palette.primary.main),
      boxSizing: 'border-box',
    },
    button2: {
      position: 'absolute',
      left: '150px',
      bottom: '10px',
      ...buttonStyle(theme, theme.palette.primary.main),
      boxSizing: 'border-box',
    },
    graph: {
      '& svg[name="svg-container-graph-id"]': {
        backgroundColor: '#fefefe',
        backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'8\' height=\'8\' viewBox=\'0 0 8 8\'%3E%3Cg fill=\'%23dedede\' fill-opacity=\'0.4\'%3E%3Cpath fill-rule=\'evenodd\' d=\'M0 0h4v4H0V0zm4 4h4v4H4V4z\'/%3E%3C/g%3E%3C/svg%3E")',
      },
    },
  }));

interface Props {
    studyId: string;
}

const fakeData = {
  nodes: [
    {
      id: 'aa',
      x: 252,
      y: 290,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'bb',
      x: 415,
      y: 290,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'cc',
      x: 113,
      y: 199,
      color: 'rgb(230, 108, 44)',
    },
    {
      id: 'dd',
      x: 265,
      y: 199,
      color: 'rgb(230, 108, 44)',
    }],
  links: [
    { source: 'aa', target: 'bb' },
    { source: 'aa', target: 'cc' },
    { source: 'aa', target: 'dd' },
  ],
};

const FONT_SIZE = 15;

const calculateSize = (text: string): number => {
  const textSize = text.length;
  if (textSize < 5) {
    return FONT_SIZE * textSize * 12;
  }
  if (textSize <= 10) {
    return FONT_SIZE * textSize * 7.5;
  }
  return FONT_SIZE * textSize * 6.5;
};

const MapView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;
  const [studyConfig, setStudyConfig] = useState<StudyProperties>();
  const [areasList, setAreasList] = useState<Array<string>>();
  const [areas, setAreas] = useState<AreasConfig>();
  const [loaded, setLoaded] = useState(false);
  const [nodeClick, setNodeClick] = useState<NodeProperties>();
  const [nodeData, setNodeData] = useState<Array<NodeProperties>>();
  const [linkData, setLinkData] = useState<Array<LinkProperties>>();
  const [linkClick, setLinkClick] = useState<LinkProperties>();
  const { enqueueSnackbar } = useSnackbar();
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [createLinkMode, setCreateLinkMode] = useState<boolean>(false);
  const [firstNode, setFirstNode] = useState<string>();
  const [secondNode, setSecondNode] = useState<string>();

  const onClickNode = (nodeId: string) => {
    if (!createLinkMode) {
      const obj = fakeData.nodes.find((o) => o.id === nodeId);
      setNodeClick(obj);
      setLinkClick(undefined);
    } else if (!firstNode) {
      setFirstNode(nodeId);
    } else if (firstNode) {
      setSecondNode(nodeId);
    }
  };

  const onClickLink = (source: string, target: string) => {
    const obj = {
      source,
      target,
    };
    setLinkClick(obj);
    setNodeClick(undefined);
  };

  const createLink = () => {
    if (createLinkMode) {
      setCreateLinkMode(false);
      setFirstNode(undefined);
      setSecondNode(undefined);
    } else {
      setCreateLinkMode(true);
    }
  };

  const onClose = () => {
    setOpenModal(false);
  };

  const onSave = (name: string, posX: number, posY: number, color: string) => {
    setOpenModal(false);
    fakeData.nodes.push({
      id: name,
      x: posX,
      y: posY,
      color,
    });
  };

  const onDelete = (id: string, target?: string) => {
    if (target) {
      const obj = fakeData.links.find((o) => o.source === id && o.target === target);
      if (obj) {
        const i = fakeData.links.indexOf(obj);
        if (i !== -1) {
          fakeData.links.splice(i, 1);
          setLinkClick(undefined);
        }
      }
    } else {
      const obj = fakeData.nodes.find((o) => o.id === id);
      const links = fakeData.links.filter((o) => o.source === id || o.target === id);
      if (obj) {
        const i = fakeData.nodes.indexOf(obj);
        if (i !== -1) {
          fakeData.nodes.splice(i, 1);
          setNodeClick(undefined);
        }
      }
      if (links) {
        // eslint-disable-next-line array-callback-return
        for (let i = 0; i < links.length; i += 1) {
          const index = fakeData.links.indexOf(links[i]);
          if (index !== -1) {
            fakeData.links.splice(index, 1);
          }
        }
      }
    }
  };

  useEffect(() => {
    if (firstNode && secondNode) {
      fakeData.links.push({
        source: firstNode,
        target: secondNode,
      });
      setCreateLinkMode(false);
      setFirstNode(undefined);
      setSecondNode(undefined);
    }
  }, [setCreateLinkMode, firstNode, secondNode]);

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getSynthesis(studyId);
        setStudyConfig(data as StudyProperties);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoloadstudy'), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    };
    init();
  }, [enqueueSnackbar, studyId, t]);

  useEffect(() => {
    if (loaded) {
      if (studyConfig) {
        setAreasList(Object.keys(studyConfig.areas));
      }
    }
  }, [loaded, studyConfig, enqueueSnackbar, t]);

  useEffect(() => {
    const init = async () => {
      try {
        if (areasList) {
          const data = await getAreaPositions(studyId, areasList.join(','));
          if (areasList.length === 1) {
            setAreas({
              [areasList[0]]: data,
            });
          } else {
            setAreas(data);
          }
        }
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoloadstudy'), e as AxiosError);
      }
    };
    init();
  }, [studyId, areasList, enqueueSnackbar, t]);

  useEffect(() => {
    if (areas) {
      const tempNodeData = Object.keys(areas).map((areaId) => ({
        id: areaId,
        x: areas[areaId].ui.x,
        y: areas[areaId].ui.y,
        color: `rgb(${areas[areaId].ui.color_r}, ${areas[areaId].ui.color_g}, ${areas[areaId].ui.color_b})`,
        size: { width: calculateSize(areaId), height: 250 },
      }));

      if (tempNodeData.length > 0) {
        const enclosingRect = tempNodeData.reduce((acc, currentNode) => ({
          xmax: acc.xmax > currentNode.x ? acc.xmax : currentNode.x,
          xmin: acc.xmin < currentNode.x ? acc.xmin : currentNode.x,
          ymax: acc.ymax > currentNode.y ? acc.ymax : currentNode.y,
          ymin: acc.ymin > currentNode.y ? acc.xmin : currentNode.y,
        }), { xmax: tempNodeData[0].x, xmin: tempNodeData[0].x, ymax: tempNodeData[0].y, ymin: tempNodeData[0].y });
        const rectCenter = { x: (enclosingRect.xmax - enclosingRect.xmin) / 2, y: (enclosingRect.ymax - enclosingRect.ymin) / 2 };
        const positionOffset = { x: enclosingRect.xmin < 0 ? enclosingRect.xmin : 0, y: enclosingRect.ymin < 0 ? enclosingRect.ymin : 0 };
        setNodeData(
          tempNodeData.map((area) => ({
            ...area,
            x: area.x - positionOffset.x + rectCenter.x,
            y: area.y - positionOffset.y + rectCenter.y,
          })),
        );
      } else {
        setNodeData(tempNodeData);
      }

      if (studyConfig) {
        setLinkData(Object.keys(studyConfig.areas).reduce((links, currentAreaId) =>
          links.concat(Object.keys(studyConfig.areas[currentAreaId].links).map((linkId) => ({
            source: currentAreaId,
            target: linkId,
          }))), [] as Array<LinkProperties>));
      }
    }
  }, [areas, studyConfig]);

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:map')}</Typography>
      </div>
      <div className={`${classes.autosizer} ${classes.graph}`}>
        {nodeData && linkData && (
          <AutoSizer>
            {
              ({ height, width }) => (
                <Graph
                  id="graph-id" // id is mandatory
                  data={{
                    nodes: nodeData,
                    links: linkData,
                  }}
                  config={{
                    height,
                    width,
                    staticGraphWithDragAndDrop: true,
                    d3: {
                    },
                    node: {
                      renderLabel: false,
                      fontSize: FONT_SIZE,
                      viewGenerator: (node) => <NodeView node={node} />,
                    },
                    link: {
                      color: '#d3d3d3',
                      strokeWidth: 2,
                    },
                  }}
                  onClickNode={onClickNode}
                  onClickLink={onClickLink}
                />
              )
            }
          </AutoSizer>
        )}

        <Button className={classes.button} onClick={() => setOpenModal(true)}>
          {t('singlestudy:newArea')}
        </Button>
        <Button className={classes.button2} onClick={createLink}>
          {t('singlestudy:newLink')}
        </Button>

        {nodeClick && (
          <PanelCardView name={t('singlestudy:area')} node={nodeClick} onClose={() => setNodeClick(undefined)} onDelete={onDelete} />
        )}

        {linkClick && (
          <PanelCardView name={t('singlestudy:link')} link={linkClick} onClose={() => setLinkClick(undefined)} onDelete={onDelete} />
        )}
      </div>
      {openModal && (
        <CreateAreaModal
          open={openModal}
          onClose={onClose}
          onSave={onSave}
        />
      )}
    </Paper>
  );
};

export default MapView;
