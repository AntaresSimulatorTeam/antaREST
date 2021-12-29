import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
} from '@material-ui/core';
import { NodeClickConfig, LinkClickConfig } from './utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
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
    popup: {
      position: 'absolute',
      right: '30px',
      top: '100px',
      width: '200px',
    },
  }));

interface PropType {
    name: string;
    node?: NodeClickConfig;
    link?: LinkClickConfig;
    onClose: () => void;
}

const PanelCardView = (props: PropType) => {
  const classes = useStyles();
  const { name, node, link, onClose } = props;

  return (
    <Card className={classes.popup}>
      <Typography className={`${classes.header} ${classes.title}`} gutterBottom>
        {name}
      </Typography>
      <CardContent>
        {node && (
          <>
            <Typography variant="h5" component="h2">
              {node.id}
            </Typography>
            <Typography variant="body2" component="p">
              {node.x}
              <br />
              {node.y}
              <br />
              {node.color}
            </Typography>
          </>
        )}
        {link && (
        <Typography variant="body2" component="p">
          {link.source}
          <br />
          {link.target}
        </Typography>
        )}
      </CardContent>
      <CardActions>
        <Button size="small">More</Button>
        <Button onClick={onClose} size="small">Close</Button>
      </CardActions>
    </Card>
  );
};

PanelCardView.defaultProps = {
  node: undefined,
  link: undefined,
};
export default PanelCardView;
