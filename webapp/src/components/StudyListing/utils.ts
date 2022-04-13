/* eslint-disable no-plusplus */
import moment from 'moment';
import { StudyMetadata } from '../../common/types';

export interface StudyTreeNode {
    name: string;
    path: string;
    modificationDate: string;
    children: Array<StudyTreeNode | StudyMetadata>;
  }

export const isDir = (element: StudyTreeNode | StudyMetadata): boolean => (element as StudyMetadata).id === undefined;

const nodeProcess = (tree: StudyTreeNode, path: Array<string>, study: StudyMetadata, folderPath: string): string => {
  const { children } = tree;
  let newModificationDate = '';
  if (path.length === 1) {
    children.push(study);
    newModificationDate = moment(tree.modificationDate).isAfter(moment(study.modificationDate)) ? tree.modificationDate : study.modificationDate;
    // eslint-disable-next-line no-param-reassign
    tree.modificationDate = newModificationDate;
    return newModificationDate;
  }
  const element = path.pop() || '';
  const index = children.findIndex((elm: StudyTreeNode | StudyMetadata) => isDir(elm) && elm.name === element);
  const newFolderPath = `${folderPath}/${element}`;
  if (index < 0) {
    children.push({ name: element, modificationDate: '', children: [], path: newFolderPath });
    newModificationDate = nodeProcess(children[children.length - 1] as StudyTreeNode, path, study, newFolderPath);
  } else {
    newModificationDate = nodeProcess(children[index] as StudyTreeNode, path, study, newFolderPath);
  }
  // eslint-disable-next-line no-param-reassign
  tree.modificationDate = moment(tree.modificationDate).isAfter(moment(newModificationDate)) ? tree.modificationDate : newModificationDate;
  return tree.modificationDate;
};

export const buildStudyTree = (studies: Array<StudyMetadata>): StudyTreeNode => {
  const tree: StudyTreeNode = { name: 'root', modificationDate: '', children: [], path: '' };
  let path: Array<string> = [];
  for (let i = 0; i < studies.length; i++) {
    if (studies[i].folder !== undefined && studies[i].folder !== null) {
      path = [studies[i].workspace, ...(studies[i].folder as string).split('/').filter((elm) => elm !== '')];
    } else {
      path = [studies[i].workspace];
    }
    path.reverse();
    nodeProcess(tree, path, studies[i], '');
  }
  return tree;
};

export interface FindNodeResult {
  path: Array<string>;
  node: StudyTreeNode | undefined;
}

export const findNode = (elements: Array<StudyTreeNode | StudyMetadata>, path: Array<string>): StudyTreeNode | undefined => {
  const tmpElm = ([] as Array<StudyTreeNode | StudyMetadata>).concat(elements);
  const element = tmpElm.pop();
  if (path.length === 0 || element === undefined) return undefined;

  const elm = path[0];
  if (element.name === elm && isDir(element)) {
    if (path.length === 1) {
      return element as StudyTreeNode;
    }
    return findNode((element as StudyTreeNode).children, path.slice(1));
  }

  return findNode(tmpElm, path);
};

export const countAllStudies = (node: StudyTreeNode): number => node.children.reduce((count, curNode) => {
  if (isDir(curNode)) {
    return count + countAllStudies(curNode as StudyTreeNode);
  }
  return count + 1;
}, 0);

export default {};
