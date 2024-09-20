# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import hashlib
import logging
import typing as t
from pathlib import Path

import numpy as np
import pandas as pd
from filelock import FileLock
from numpy import typing as npt
from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import Matrix, MatrixContent, MatrixData, MatrixDataSet

logger = logging.getLogger(__name__)


class MatrixDataSetRepository:
    """
    Database connector to manage Matrix metadata entity
    """

    def __init__(self, session: t.Optional[Session] = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, matrix_user_metadata: MatrixDataSet) -> MatrixDataSet:
        res: bool = self.session.query(exists().where(MatrixDataSet.id == matrix_user_metadata.id)).scalar()
        if res:
            matrix_user_metadata = self.session.merge(matrix_user_metadata)
        else:
            self.session.add(matrix_user_metadata)
        self.session.commit()

        logger.debug(f"Matrix dataset {matrix_user_metadata.id} for user {matrix_user_metadata.owner_id} saved")
        return matrix_user_metadata

    def get(self, id_number: str) -> t.Optional[MatrixDataSet]:
        matrix: MatrixDataSet = self.session.query(MatrixDataSet).get(id_number)
        return matrix

    def get_all_datasets(self) -> t.List[MatrixDataSet]:
        matrix_datasets: t.List[MatrixDataSet] = self.session.query(MatrixDataSet).all()
        return matrix_datasets

    def query(
        self,
        name: t.Optional[str],
        owner: t.Optional[int] = None,
    ) -> t.List[MatrixDataSet]:
        """
        Query a list of MatrixUserMetadata by searching for each one separately if a set of filter match

        Parameters:
            name: the partial name of dataset
            owner: owner id to filter the result with

        Returns:
            the list of metadata per user, matching the query
        """
        query = self.session.query(MatrixDataSet)
        if name is not None:
            query = query.filter(MatrixDataSet.name.ilike(f"%{name}%"))  # type: ignore
        if owner is not None:
            query = query.filter(MatrixDataSet.owner_id == owner)
        datasets: t.List[MatrixDataSet] = query.distinct().all()
        return datasets

    def delete(self, dataset_id: str) -> None:
        dataset = self.session.query(MatrixDataSet).get(dataset_id)
        self.session.delete(dataset)
        self.session.commit()


class MatrixRepository:
    """
    Database connector to manage Matrix entity.
    """

    def __init__(self, session: t.Optional[Session] = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, matrix: Matrix) -> Matrix:
        if self.session.query(exists().where(Matrix.id == matrix.id)).scalar():
            self.session.merge(matrix)
        else:
            self.session.add(matrix)
        self.session.commit()

        logger.debug(f"Matrix {matrix.id} saved")
        return matrix

    def get(self, matrix_hash: str) -> t.Optional[Matrix]:
        matrix: Matrix = self.session.query(Matrix).get(matrix_hash)
        return matrix

    def exists(self, matrix_hash: str) -> bool:
        res: bool = self.session.query(exists().where(Matrix.id == matrix_hash)).scalar()
        return res

    def delete(self, matrix_hash: str) -> None:
        if g := self.session.query(Matrix).get(matrix_hash):
            self.session.delete(g)
            self.session.commit()
        else:
            logger.warning(f"Trying to delete matrix {matrix_hash}, but was not found in database!")
        logger.debug(f"Matrix {matrix_hash} deleted")


class MatrixContentRepository:
    """
    Manage the content of matrices stored in a directory.

    This class provides methods to get, check existence,
    save, and delete the content of matrices stored in a directory.
    The matrices are stored as Hierarchical Data Format (HDF) files and
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

        Parameters:
            matrix_hash: SHA256 hash

        Returns:
            The matrix content or `None` if the file is not found.
        """

        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.hdf")
        if matrix_file.stat().st_size == 0:  # hdf5 doesn't support reading empty files.
            data: t.List[t.List[int]] = [[]]
            columns = []
            index = [0]
        else:
            df = t.cast(pd.DataFrame, pd.read_hdf(matrix_file))
            data = df.values.tolist()
            index = list(range(df.shape[0]))
            columns = list(range(df.shape[1]))
        return MatrixContent.construct(data=data, columns=columns, index=index)

    def exists(self, matrix_hash: str) -> bool:
        """
        Checks if a matrix with a given SHA256 hash exists in the directory.

        Parameters:
            matrix_hash: SHA256 hash

        Returns:
            `True` if the matrix exist else `None`.
        """
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.hdf")
        return matrix_file.exists()

    def save(self, content: t.Union[t.List[t.List[MatrixData]], npt.NDArray[np.float64]]) -> str:
        """
        Saves the content of a matrix as an HDF file in the bucket directory
        and returns its SHA256 hash.

        The matrix content will be saved in an HDF file format, where each row represents
        a line in the file and the values are separated by tabs. The file will be saved
        in the bucket directory using a unique filename. The SHA256 hash of the NumPy array
        is returned as a string.

        Parameters:
            content:
                The matrix content to be saved. It can be either a nested list of floats
                or a NumPy array of type np.float64.

        Returns:
            The SHA256 hash of the saved HDF file.

        Raises:
            ValueError:
                If the provided content is not a valid matrix or cannot be saved.
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
        matrix = content if isinstance(content, np.ndarray) else np.array(content, dtype=np.float64)
        matrix_hash = hashlib.sha256(matrix.data).hexdigest()
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.hdf")
        # Avoid having to save the matrix again (that's the whole point of using a hash).
        if not matrix_file.exists():
            # Ensure exclusive access to the matrix file between multiple processes (or threads).
            lock_file = matrix_file.with_suffix(".hdf.lock")
            with FileLock(lock_file, timeout=15):
                if matrix.size == 0:
                    matrix_file.touch()
                else:
                    df = pd.DataFrame(matrix)
                    df.to_hdf(str(matrix_file), "data")

            # IMPORTANT: Deleting the lock file under Linux can make locking unreliable.
            # See https://github.com/tox-dev/py-filelock/issues/31
            # However, this deletion is possible when the matrix is no longer in use.
            # This is done in `MatrixGarbageCollector` when matrix files are deleted.

        return matrix_hash

    def delete(self, matrix_hash: str) -> None:
        """
        Deletes the HDF file containing the content of a matrix with the given SHA256 hash.

        Parameters:
            matrix_hash: The SHA256 hash of the matrix.

        Raises:
            FileNotFoundError: If the HDF file does not exist.

        Note:
            This method also deletes any abandoned lock file.
        """
        matrix_file = self.bucket_dir.joinpath(f"{matrix_hash}.hdf")
        matrix_file.unlink()

        # IMPORTANT: Deleting the lock file under Linux can make locking unreliable.
        # Abandoned lock files are deleted here to maintain consistent behavior.
        lock_file = matrix_file.with_suffix(".hdf.lock")
        lock_file.unlink(missing_ok=True)
