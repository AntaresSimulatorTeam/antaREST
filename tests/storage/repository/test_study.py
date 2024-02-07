from datetime import datetime

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study, StudyContentStatus
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.helpers import with_db_context


@with_db_context
def test_lifecycle() -> None:
    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    repo = StudyMetadataRepository(LocalCache())
    a = Study(
        name="a",
        version="42",
        author="John Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )
    b = RawStudy(
        name="b",
        version="43",
        author="Morpheus",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )
    c = RawStudy(
        name="c",
        version="43",
        author="Trinity",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
        missing=datetime.utcnow(),
    )
    d = VariantStudy(
        name="d",
        version="43",
        author="Mr. Anderson",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )

    a = repo.save(a)
    b = repo.save(b)
    repo.save(c)
    repo.save(d)
    assert b.id
    c = repo.one(a.id)
    assert a == c

    assert len(repo.get_all()) == 4
    assert len(repo.get_all_raw(exists=True)) == 1
    assert len(repo.get_all_raw(exists=False)) == 1
    assert len(repo.get_all_raw()) == 2

    repo.delete(a.id)
    assert repo.get(a.id) is None


@with_db_context
def test_study_inheritance() -> None:
    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    repo = StudyMetadataRepository(LocalCache())
    a = RawStudy(
        name="a",
        version="42",
        author="John Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
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
