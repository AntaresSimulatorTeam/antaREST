import hashlib
import json
import logging
import os
from typing import Optional, List

from sqlalchemy import exists, and_  # type: ignore

from antarest.common.config import Config
from antarest.common.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import (
    Matrix,
    MatrixFreq,
    MatrixContent, MatrixMetadataOwnership,
)


class MatrixMetadataOwnershipRepository:
    """
    Database connector to manage Matrix metadata entity
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def save(self, matrix_ownership: MatrixMetadataOwnership) -> Matrix:
        res = db.session.query(exists().where(and_(MatrixMetadataOwnership.id == matrix_ownership.id, MatrixMetadataOwnership.owner_id == matrix_ownership.owner_id))).scalar()
        if res:
            db.session.merge(matrix_ownership)
        else:
            db.session.add(matrix_ownership)
        db.session.commit()

        self.logger.debug(f"Matrix ownership between matrix {matrix_ownership.matrix_id} and {matrix_ownership.owner_id} saved")
        return matrix_ownership

    def get(self, matrix_id: str, owner_id: int) -> Optional[MatrixMetadataOwnership]:
        matrix: MatrixMetadataOwnership = db.session.query(MatrixMetadataOwnership).get(id)
        return matrix

    def exists(self, id: str) -> bool:
        res: bool = db.session.query(exists().where(Matrix.id == id)).scalar()
        return res

class MatrixRepository:
    """
    Database connector to manage Matrix entity.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Hello")

    def save(self, matrix: Matrix) -> Matrix:
        res = db.session.query(exists().where(Matrix.id == matrix.id)).scalar()
        if res:
            db.session.merge(matrix)
        else:
            db.session.add(matrix)
        db.session.commit()

        self.logger.debug(f"Matrix {matrix.id} saved")
        return matrix

    def get(self, id: str) -> Optional[Matrix]:
        matrix: Matrix = db.session.query(Matrix).get(id)
        return matrix

    def exists(self, id: str) -> bool:
        res: bool = db.session.query(exists().where(Matrix.id == id)).scalar()
        return res

    def get_by_freq(
        self,
        freq: Optional[MatrixFreq] = None,
    ) -> List[Matrix]:
        matrix: List[Matrix] = (
            db.session.query(Matrix).filter((Matrix.freq == freq)).all()
        )
        return matrix

    def delete(self, id: str) -> None:
        g = db.session.query(Matrix).get(id)
        db.session.delete(g)
        db.session.commit()

        self.logger.debug(f"Matrix {id} deleted")


class MatrixContentRepository:
    def __init__(self, config: Config) -> None:
        self.bucket = config.matrixstore.bucket
        self.bucket.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _compute_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, id: str) -> Optional[MatrixContent]:
        file = self.bucket / id
        if not file.exists():
            return None

        data = json.load(open(file))
        return MatrixContent.from_dict(data)  # type: ignore

    def save(self, content: MatrixContent) -> str:
        stringify = content.to_json()
        h = MatrixContentRepository._compute_hash(stringify)
        (self.bucket / h).write_text(stringify)

        return h

    def delete(self, id: str) -> None:
        file = self.bucket / id
        if file.exists():
            os.remove(file)
