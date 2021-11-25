import React, { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../App/reducers';
import GenericListingView from '../../ui/NavComponents/GenericListingView';
import GroupModal from './GroupModal';
import { getGroups, createGroup, updateGroup, deleteGroup, getGroupInfos } from '../../../services/api/user';
import { GroupDTO, RoleType, UserGroup } from '../../../common/types';
import ConfirmationModal from '../../ui/ConfirmationModal';
import UserGroupView from '../UserGroupView';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { isUserAdmin } from '../../../services/utils';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

interface UserDeletion {
  groupId: string;
  userId: number;
}

interface DeletionInfo {
  type: 'user' | 'group';
  data: string | UserDeletion;
}

const GroupsSettings = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  // Group modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [groupList, setGroupList] = useState<Array<UserGroup>>([]);
  const [selectedGroup, setActiveGroup] = useState<GroupDTO>();
  const [deletionInfo, setDeletionInfo] = useState<DeletionInfo>({ type: 'group', data: '' });
  const [filter, setFilter] = useState<string>('');
  const { user } = props;

  const createNewGroup = () => {
    setOpenModal(true);
    setActiveGroup(undefined);
  };

  const onUpdateClick = (groupId: string) => {
    const groupFound = groupList.find((item) => item.group.id === groupId);

    if (groupFound) {
      setActiveGroup(groupFound.group);
      setOpenModal(true);
    }
  };

  const onDeleteGroupClick = (id: string) => {
    setDeletionInfo({ type: 'group', data: id });
    setOpenConfirmationModal(true);
  };

  const onDeleteUserClick = (groupId: string, userId: number) => {
    setDeletionInfo({ type: 'user', data: { groupId, userId } });
    setOpenConfirmationModal(true);
    // setIdForDeletion(-1);
    // setOpenConfirmationModal(false);
  };

  const manageUserDeletion = async () => {
    try {
      // setUserList(userList.filter((item) => item.id !== idForDeletion));
      const data: UserDeletion = deletionInfo.data as UserDeletion;
      console.log('DELETE USER ', data.userId, ' FROM GROUP ', data.groupId);
      enqueueSnackbar(t('settings:onUserDeleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onUserDeleteError'), e as AxiosError);
    }
    setDeletionInfo({ type: 'group', data: '' });
    setOpenConfirmationModal(false);
  };

  const manageGroupDeletion = async () => {
    try {
      // 1) Call backend (Delete)
      const deletedGroupId = await deleteGroup(deletionInfo.data as string);
      // 2) Delete group locally from groupList
      setGroupList(groupList.filter((item) => item.group.id !== deletedGroupId));
      enqueueSnackbar(t('settings:onGroupDeleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onGroupDeleteError'), e as AxiosError);
    }
    setDeletionInfo({ type: 'group', data: '' });
    setOpenConfirmationModal(false);
  };

  const onItemClick = async (groupId: string) => {
    try {
      const tmpList = ([] as Array<UserGroup>).concat(groupList);
      const groupInfos = await getGroupInfos(groupId);
      const index = tmpList.findIndex((item) => item.group.id === groupInfos.group.id);
      if (index >= 0) {
        tmpList[index] = { group: groupInfos.group, users: groupInfos.users.filter((elm) => elm.id !== user?.id) };
        setGroupList(tmpList);
      } else {
        enqueueSnackbar(t('settings:groupInfosError'), { variant: 'error' });
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:groupInfosError'), e as AxiosError);
    }
  };

  const onModalClose = () => {
    setOpenModal(false);
  };

  const onModalSave = async (name: string) => {
    try {
      if (selectedGroup) {
        if (selectedGroup.name === name) return;

        const updatedGroup = await updateGroup(selectedGroup.id, name);
        const tmpList = ([] as Array<UserGroup>).concat(groupList);
        const index = tmpList.findIndex((item) => item.group.id === selectedGroup.id);
        if (index >= 0) {
          tmpList[index].group.name = updatedGroup.name;
          setGroupList(tmpList);
          enqueueSnackbar(t('settings:onGroupUpdate'), { variant: 'success' });
        }
      } else {
        const newGroup = await createGroup(name);
        const newGroupItem: UserGroup = {
          group: newGroup,
          users: [],
        };
        setGroupList(groupList.concat(newGroupItem));
        setActiveGroup(newGroup);
        enqueueSnackbar(t('settings:onGroupCreation'), { variant: 'success' });
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onGroupSaveError'), e as AxiosError);
    }
    onModalClose();
  };

  useEffect(() => {
    const init = async () => {
      if (user !== undefined) {
        let groups: Array<UserGroup> = [];
        if (isUserAdmin(user)) {
          try {
            const res = await getGroups();
            groups = res
              .filter((item) => item.id !== 'admin')
              .map((group) => ({ group, users: [] }));
          } catch (e) {
            enqueueErrorSnackbar(enqueueSnackbar, t('settings:groupsError'), e as AxiosError);
          }
        } else {
          groups = user.groups
            .filter((item) => item.role === RoleType.ADMIN)
            .map((group) => ({ group: { id: group.id, name: group.name }, users: [] }));
        }
        setGroupList(groups);
      }
    };
    init();
  }, [user, t, enqueueSnackbar]);

  return (
    <GenericListingView
      searchFilter={(input: string) => setFilter(input)}
      placeholder={t('settings:groupsSearchbarPlaceholder')}
      buttonValue={t('settings:createGroup')}
      onButtonClick={createNewGroup}
    >
      <UserGroupView
        data={groupList}
        filter={filter}
        onDeleteGroupClick={user !== undefined && isUserAdmin(user) ? onDeleteGroupClick : undefined}
        onDeleteUserClick={onDeleteUserClick}
        onUpdateClick={onUpdateClick}
        onItemClick={onItemClick}
      />
      {openModal && (
        <GroupModal
          open={openModal}
          onClose={onModalClose}
          onSave={onModalSave}
          group={selectedGroup}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={deletionInfo.type === 'group' ? t('settings:deleteGroupConfirmation') : t('settings:deleteUserConfirmation')}
          handleYes={deletionInfo.type === 'group' ? manageGroupDeletion : manageUserDeletion}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </GenericListingView>
  );
};

export default connector(GroupsSettings);
