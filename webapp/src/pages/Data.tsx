// import { useTranslation } from "react-i18next";
// import UnderConstruction from "../components/common/page/UnderConstruction";

// function Data() {
//   const [t] = useTranslation();

//   return (
//     <RootPage title={t("main:data")} titleIcon={StorageIcon}>
//       <UnderConstruction />
//     </RootPage>
//   );
// }

// export default Data;

import { useState, useEffect } from "react";
import { connect, ConnectedProps } from "react-redux";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import StorageIcon from "@mui/icons-material/Storage";
import { AppState } from "../store/reducers";
import DataView from "../components/data/DataView";
import { deleteDataSet, getMatrixList } from "../services/api/matrix";
import { MatrixDataSetDTO, IDType, MatrixInfoDTO } from "../common/types";
import DataModal from "../components/data/DataModal";
import ConfirmationDialog from "../components/common/dialogs/ConfirmationDialog";
import RootPage from "../components/common/page/RootPage";
import MatrixModal from "../components/data/MatrixModal";
import useEnqueueErrorSnackbar from "../hooks/useEnqueueErrorSnackbar";

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function Data(props: PropTypes) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [dataList, setDataList] = useState<Array<MatrixDataSetDTO>>([]);
  const [idForDeletion, setIdForDeletion] = useState<IDType>(-1);
  const [filter, setFilter] = useState<string>("");
  const { user } = props;

  // User modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);
  const [matrixModal, setMatrixModal] = useState<boolean>(false);
  const [currentData, setCurrentData] = useState<
    MatrixDataSetDTO | undefined
  >();
  const [currentMatrix, setCurrentMatrix] = useState<
    MatrixInfoDTO | undefined
  >();

  const createNewData = () => {
    setCurrentData(undefined);
    setOpenModal(true);
  };

  const onUpdateClick = (id: IDType): void => {
    setCurrentData(dataList.find((item) => item.id === id));
    setOpenModal(true);
  };

  const onDeleteClick = (id: IDType) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  };

  const manageDataDeletion = async () => {
    try {
      await deleteDataSet(idForDeletion as string);
      setDataList(dataList.filter((item) => item.id !== idForDeletion));
      enqueueSnackbar(t("data:onMatrixDeleteSuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("data:onMatrixDeleteError"), e as AxiosError);
    }
    setIdForDeletion(-1);
    setOpenConfirmationModal(false);
  };

  const onModalClose = () => {
    setOpenModal(false);
  };

  const onMatrixModalClose = () => {
    setCurrentMatrix(undefined);
    setMatrixModal(false);
  };

  const onNewDataUpdate = (newData: MatrixDataSetDTO): void => {
    const tmpList = ([] as Array<MatrixDataSetDTO>).concat(dataList);
    const index = tmpList.findIndex((elm) => elm.id === newData.id);
    if (index >= 0) {
      tmpList[index] = newData;
      setDataList(tmpList);
    } else {
      setDataList(dataList.concat(newData));
    }
  };

  const onMatrixClick = async (matrixInfo: MatrixInfoDTO) => {
    setCurrentMatrix(matrixInfo);
    setMatrixModal(true);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const matrix = await getMatrixList();
        setDataList(matrix);
      } catch (e) {
        enqueueErrorSnackbar(t("data:matrixError"), e as AxiosError);
      }
    };
    init();
    return () => {
      setDataList([]);
    };
  }, [user, t, enqueueErrorSnackbar]);

  return (
    <RootPage title={t("main:data")} titleIcon={StorageIcon}>
      <DataView
        data={dataList}
        filter={filter}
        user={user}
        onDeleteClick={onDeleteClick}
        onUpdateClick={onUpdateClick}
        onMatrixClick={onMatrixClick}
      />
      {matrixModal && currentMatrix && (
        <MatrixModal
          open={matrixModal} // Why 'openModal &&' ? => Otherwise previous data are still present
          matrixInfo={currentMatrix}
          onClose={onMatrixModalClose}
        />
      )}
      {openModal && (
        <DataModal
          open={openModal} // Why 'openModal &&' ? => Otherwise previous data are still present
          data={currentData}
          onNewDataUpdate={onNewDataUpdate}
          onClose={onModalClose}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          onConfirm={() => {
            manageDataDeletion();
            setOpenConfirmationModal(false);
          }}
          onCancel={() => setOpenConfirmationModal(false)}
          alert="warning"
        >
          {t("data:deleteMatrixConfirmation")}
        </ConfirmationDialog>
      )}
    </RootPage>
  );
}

export default connector(Data);
