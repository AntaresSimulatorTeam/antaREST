import datetime
import logging
import typing as t
from typing import List, Tuple, Union

from sqlalchemy import select, func
from sqlalchemy import and_, or_  # type: ignore
from sqlalchemy.orm import Session, joinedload, with_polymorphic  # type: ignore

from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.common.utils import get_study_information
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study, StudyAdditionalData

logger = logging.getLogger(__name__)


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self, cache_service: ICache, session: t.Optional[Session] = None):
        """
        Initialize the repository.

        Args:
            cache_service: Cache service for the repository.
            session: Optional SQLAlchemy session to be used.
        """
        self.cache_service = cache_service
        self._session = session

    @property
    def session(self) -> Session:
        """
        Get the SQLAlchemy session for the repository.

        Returns:
            SQLAlchemy session.
        """
        if self._session is None:
            # Get or create the session from a context variable (thread local variable)
            return db.session
        # Get the user-defined session
        return self._session

    def save(
        self,
        metadata: Study,
        update_modification_date: bool = False,
        update_in_listing: bool = True,
    ) -> Study:
        metadata_id = metadata.id or metadata.name
        logger.debug(f"Saving study {metadata_id}")
        if update_modification_date:
            metadata.updated_at = datetime.datetime.utcnow()

        session = self.session
        metadata.groups = [session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = session.merge(metadata.owner)
        session.add(metadata)
        session.commit()

        if update_in_listing:
            self._update_study_from_cache_listing(metadata)
        return metadata

    def refresh(self, metadata: Study) -> None:
        self.session.refresh(metadata)

    def get(self, id: str) -> t.Optional[Study]:
        """Get the study by ID or return `None` if not found in database."""
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        study: Study = (
            # fmt: off
            self.session.query(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .get(id)
            # fmt: on
        )
        return study

    def one(self, study_id: str) -> Study:
        """Get the study by ID or raise `sqlalchemy.exc.NoResultFound` if not found in database."""
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        study: Study = (
            self.session.query(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .filter_by(id=study_id)
            .one()
        )
        return study

    def get_additional_data(self, study_id: str) -> t.Optional[StudyAdditionalData]:
        study: StudyAdditionalData = self.session.query(StudyAdditionalData).get(study_id)
        return study

    def get_all(
        self,
        managed: t.Optional[bool] = None,
        studies_ids: t.Optional[t.List[str]] = None,
        exists: bool = True,
    ) -> t.List[Study]:
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        # We also need to fetch the additional data to display the study information
        # efficiently (see: `utils.get_study_information`)
        entity = with_polymorphic(Study, "*")

        q = self.session.query(entity)
        if exists:
            q = q.filter(RawStudy.missing.is_(None))
        q = q.options(joinedload(entity.owner))
        q = q.options(joinedload(entity.groups))
        q = q.options(joinedload(entity.additional_data))
        if managed is not None:
            if managed:
                q = q.filter(or_(entity.type == "variantstudy", RawStudy.workspace == DEFAULT_WORKSPACE_NAME))
            else:
                q = q.filter(entity.type == "rawstudy")
                q = q.filter(RawStudy.workspace != DEFAULT_WORKSPACE_NAME)
        if studies_ids is not None:
            q = q.filter(entity.id.in_(studies_ids))
        studies: t.List[Study] = q.all()
        return studies

    def get_all_raw(self, show_missing: bool = True) -> t.List[RawStudy]:
        query = self.session.query(RawStudy)
        if not show_missing:
            query = query.filter(RawStudy.missing.is_(None))
        studies: t.List[RawStudy] = query.all()
        return studies

    def delete(self, ids: Union[str, List[str]]) -> None:
        logger.debug(f"Deleting study {id}")
        if isinstance(ids, str):
            # if id is str, convert it to list with one element
            ids = [ids]
        session = self.session
        for study_id in ids:
            study: Study = session.query(Study).get(study_id)
            if study:
                session.delete(study)
                self._remove_study_from_cache_listing(study_id)
        session.commit()

    def _remove_study_from_cache_listing(self, study_id: str) -> None:
        try:
            cached_studies = self.cache_service.get(CacheConstants.STUDY_LISTING.value)
            if cached_studies:
                if study_id in cached_studies:
                    del cached_studies[study_id]
                self.cache_service.put(CacheConstants.STUDY_LISTING.value, cached_studies)
        except Exception as e:
            logger.error("Failed to update study listing cache", exc_info=e)
            try:
                self.cache_service.invalidate(CacheConstants.STUDY_LISTING.value)
            except Exception as e:
                logger.error("Failed to invalidate listing cache", exc_info=e)

    def _update_study_from_cache_listing(self, study: Study) -> None:
        try:
            cached_studies = self.cache_service.get(CacheConstants.STUDY_LISTING.value)
            if cached_studies:
                if isinstance(study, RawStudy) and study.missing is not None:
                    del cached_studies[study.id]
                else:
                    cached_studies[study.id] = get_study_information(study)
                self.cache_service.put(CacheConstants.STUDY_LISTING.value, cached_studies)
        except Exception as e:
            logger.error("Failed to update study listing cache", exc_info=e)
            try:
                self.cache_service.invalidate(CacheConstants.STUDY_LISTING.value)
            except Exception as e:
                logger.error("Failed to invalidate listing cache", exc_info=e)

    def list_duplicates(self) -> List[Tuple[str, str]]:
        """
            Get list of duplicates as tuples (id, path).
        """
        session = self.session
        subquery = (
            session.query(Study.path)
            .group_by(Study.path)
            .having(func.count()>1)
            .subquery()
        )
        query = (
            session.query(Study.id, Study.path)
            .filter(Study.path.in_(subquery))
        )
        return query.all()
