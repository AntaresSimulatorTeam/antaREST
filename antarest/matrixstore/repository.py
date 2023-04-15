import hashlib
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import (
    Matrix,
    MatrixContent,
    MatrixData,
    MatrixDataSet,
)
from sqlalchemy import and_, exists  # type: ignore
from sqlalchemy.orm import aliased  # type: ignore

logger = logging.getLogger(__name__)


class MatrixDataSetRepository:
    """
    Database connector to manage Matrix metadata entity
    """

    def save(self, matrix_user_metadata: MatrixDataSet) -> MatrixDataSet:
        res: bool = db.session.query(
            exists().where(MatrixDataSet.id == matrix_user_metadata.id)
        ).scalar()
        if res:
            matrix_user_metadata = db.session.merge(matrix_user_metadata)
        else:
            db.session.add(matrix_user_metadata)
        db.session.commit()

        logger.debug(
            f"Matrix dataset {matrix_user_metadata.id} for user {matrix_user_metadata.owner_id} saved"
        )
        return matrix_user_metadata

    def get(self, id: str) -> Optional[MatrixDataSet]:
        matrix: MatrixDataSet = db.session.query(MatrixDataSet).get(id)
        return matrix

    def get_all_datasets(self) -> List[MatrixDataSet]:
        matrix_datasets: List[MatrixDataSet] = db.session.query(
            MatrixDataSet
        ).all()
        return matrix_datasets

    def query(
        self,
        name: Optional[str],
        owner: Optional[int] = None,
    ) -> List[MatrixDataSet]:
        """
        Query a list of MatrixUserMetadata by searching for each one separatly if a set of filter match
        Args:
            name: the partial name of dataset
            owner: owner id to filter the result with

        Returns:
            the list of metadata per user, matching the query
        """
        query = db.session.query(MatrixDataSet)
        if name is not None:
            query = query.filter(MatrixDataSet.name.ilike(f"%{name}%"))
        if owner is not None:
            query = query.filter(MatrixDataSet.owner_id == owner)
        datasets: List[MatrixDataSet] = query.distinct().all()
        return datasets

    def delete(self, dataset_id: str) -> None:
        dataset = db.session.query(MatrixDataSet).get(dataset_id)
        db.session.delete(dataset)
        db.session.commit()


class MatrixRepository:
    """
    Database connector to manage Matrix entity.
    """

    def save(self, matrix: Matrix) -> Matrix:
        if db.session.query(exists().where(Matrix.id == matrix.id)).scalar():
            db.session.merge(matrix)
        else:
            db.session.add(matrix)
        db.session.commit()

        logger.debug(f"Matrix {matrix.id} saved")
        return matrix

    def get(self, matrix_hash: str) -> Optional[Matrix]:
        matrix: Matrix = db.session.query(Matrix).get(matrix_hash)
        return matrix

    def exists(self, matrix_hash: str) -> bool:
        res: bool = db.session.query(
            exists().where(Matrix.id == matrix_hash)
        ).scalar()
        return res

    def delete(self, matrix_hash: str) -> None:
        if g := db.session.query(Matrix).get(matrix_hash):
            db.session.delete(g)
            db.session.commit()
        else:
            logger.warning(
                f"Trying to delete matrix {matrix_hash}, but was not found in database!"
            )
        logger.debug(f"Matrix {matrix_hash} deleted")


class MatrixContentRepository:
    """
    Manage the content of matrices stored in a directory.

    This class provides methods to get, check existence,
    save, and delete the content of matrices stored in a directory.
    The matrices are stored as tab-separated values (TSV) files and
    are accessed and modified using their SHA256 hash as their unique identifier.

    Attributes:
        bucket_dir: The directory path where the matrices are stored.
    """

    def __init__(self, bucket_dir: Path) -> None:
        self.bucket_dir = bucket_dir
        self.bucket_dir.mkdir(parents=True, exist_ok=True)

    def get(self, matrix_hash: str) -> MatrixContent:
        """
        Retrieves the content of a matrix with a given SHA256 hash.

        Args:
            matrix_hash: SHA256 hash

        Returns:
            The matrix content or `None` if the file is not found.
        """
        # fmt: off
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.tsv")
        matrix = np.loadtxt(matrix_file, delimiter="\t", dtype=np.float64, ndmin=2)
        data = matrix.tolist()
        index = list(range(matrix.shape[0]))
        columns = list(range(matrix.shape[1]))
        return MatrixContent.construct(data=data, columns=columns, index=index)
        # fmt: on

    def exists(self, matrix_hash: str) -> bool:
        """
        Checks if a matrix with a given SHA256 hash exists in the directory.

        Args:
            matrix_hash: SHA256 hash

        Returns:
            `True` if the matrix exist else `None`.
        """
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.tsv")
        return matrix_file.exists()

    def save(self, content: List[List[MatrixData]]) -> str:
        """
        Saves the content of a matrix as a TSV file in the directory
        and returns its SHA256 hash.

        Args:
            content: matrix data

        Returns:
            SHA256 hash
        """
        # IMPLEMENTATION DETAIL:
        # We chose to calculate the hash value from the binary data of the array buffer,
        # as this is much more efficient than using a JSON string conversion.
        # Note that in both cases, the hash value calculation is not stable:
        # 1. The same floating point number can have several possible representations
        #    depending on the platform on which the calculations are performed,
        # 2. The JSON conversion, necessarily involves a textual representation
        #    of the floating point numbers which can introduce rounding errors.
        # However, this method is still a good approach to calculate a hash value
        # for a non-mutable NumPy Array.
        matrix = np.array(content, dtype=np.float64)
        matrix_hash = hashlib.sha256(matrix.data).hexdigest()
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.tsv")
        # noinspection PyTypeChecker
        np.savetxt(matrix_file, matrix, delimiter="\t", fmt="%.18g")
        return matrix_hash

    def delete(self, matrix_hash: str) -> None:
        """
        Deletes the tsv file containing the content of a matrix with a given SHA256 hash.

        Args:
            matrix_hash: SHA256 hash
        """
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.tsv")
        matrix_file.unlink()
