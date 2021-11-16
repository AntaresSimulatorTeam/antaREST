import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { connect, ConnectedProps } from 'react-redux';
import { findNode, isDir, StudyTreeNode } from '../utils';
import DirView from './DirView';
import { StudyMetadata } from '../../../common/types';
import { AppState } from '../../../App/reducers';
import { updateFolderPosition } from '../../../ducks/study';

const mapState = (state: AppState) => ({
  directory: state.study.directory,
});

const mapDispatch = ({
  updateFolderPos: updateFolderPosition,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  tree: StudyTreeNode;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyDirView = (props: PropTypes) => {
  const history = useHistory();
  const { tree, updateFolderPos, directory } = props;
  const [dirPath, setDirPath] = useState<Array<string>>([tree.name]);
  const [currentNode, setCurrentNode] = useState<StudyTreeNode>(tree);

  const onClick = (element: StudyTreeNode | StudyMetadata): void => {
    if (isDir(element)) {
      setCurrentNode(element as StudyTreeNode);
      const newPath: Array<string> = dirPath.concat([element.name]);
      setDirPath(newPath);
      updateFolderPos(newPath.join('/'));
    } else {
      history.push(`/study/${encodeURI((element as StudyMetadata).id)}`);
    }
  };

  const onDirClick = (elements: Array<string>): void => {
    const node = findNode([tree], elements);
    setCurrentNode(node as StudyTreeNode);
    setDirPath(elements);
    updateFolderPos(elements.join('/'));
  };

  const updateTree = useCallback((element: Array<string>, treeElement: StudyTreeNode): void => {
    const node = findNode([treeElement], element);
    if (node !== undefined) {
      setCurrentNode(node);
      setDirPath(element);
    } else {
      setCurrentNode(treeElement);
      setDirPath([treeElement.name]);
    }
  }, []);

  useEffect(() => {
    updateTree(dirPath, tree);
  }, [dirPath, tree, updateTree]);

  useEffect(() => {
    const tmpTab = directory.split('/');
    if (tmpTab.length > 0) {
      updateTree(tmpTab, tree);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <DirView
      dirPath={dirPath}
      node={currentNode}
      onClick={onClick}
      onDirClick={onDirClick}
    />
  );
};

export default connector(StudyDirView);
