from typing import Optional, List

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
    CommandBlock,
    VariantStudySnapshot,
)


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant  study repository
    """

    def get_children(self, parent_id: str) -> List[VariantStudy]:
        studies: List[VariantStudy] = (
            db.session.query(VariantStudy)
            .filter(VariantStudy.parent_id == parent_id)
            .all()
        )
        return studies

    def get_snapshot(self, id: str) -> VariantStudySnapshot:
        snapshot: VariantStudySnapshot = (
            db.session.query(VariantStudySnapshot)
            .filter(VariantStudySnapshot.id == id)
            .all()
        )
        return snapshot

    def delete_snapshot(self, id: str) -> None:
        snapshot: VariantStudySnapshot = db.session.query(
            VariantStudySnapshot
        ).get(id)
        db.session.delete(snapshot)
        db.session.commit()
