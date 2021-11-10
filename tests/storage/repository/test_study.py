from datetime import datetime
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker  # type: ignore

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.login.model import User, Group
from antarest.study.model import (
    Study,
    RawStudy,
    DEFAULT_WORKSPACE_NAME,
    StudyContentStatus,
    PublicMode,
)
from antarest.study.repository import StudyMetadataRepository


def test_cyclelife():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = StudyMetadataRepository(LocalCache())
        a = Study(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )
        b = Study(
            name="b",
            version="43",
            author="Morpheus",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )

        a = repo.save(a)
        b = repo.save(b)
        assert b.id
        c = repo.get(a.id)
        assert a == c

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_study_inheritance():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = StudyMetadataRepository(LocalCache())
        a = RawStudy(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            workspace=DEFAULT_WORKSPACE_NAME,
            path="study",
            content_status=StudyContentStatus.WARNING,
        )

        repo.save(a)
        b = repo.get(a.id)

        assert isinstance(b, RawStudy)
        assert b.path == "study"
