from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import db, DBSessionMiddleware
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.repository import JobResultRepository


@pytest.mark.unit_test
def test_job_result() -> None:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = JobResultRepository()
        study_id = str(uuid4())
        a = JobResult(
            id=str(uuid4()),
            study_id=study_id,
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
        )
        b = JobResult(
            id=str(uuid4()),
            study_id=study_id,
            job_status=JobStatus.FAILED,
            msg="You failed !!",
            exit_code=1,
        )
        b2 = JobResult(
            id=str(uuid4()),
            study_id=study_id,
            job_status=JobStatus.FAILED,
            msg="You failed !!",
            exit_code=1,
        )
        b3 = JobResult(
            id=str(uuid4()),
            study_id="other_study",
            job_status=JobStatus.FAILED,
            msg="You failed !!",
            exit_code=1,
        )

        a = repo.save(a)
        b = repo.save(b)
        b2 = repo.save(b2)
        b3 = repo.save(b3)
        c = repo.get(a.id)
        assert a == c

        d = repo.find_by_study(study_id)
        assert len(d) == 3
        assert a == d[0]

        repo.delete(a.id)
        assert repo.get(a.id) is None

        assert len(repo.find_by_study(study_id)) == 2

        repo.delete_by_study_id(study_id=study_id)
        assert repo.get(b.id) is None
        assert repo.get(b2.id) is None
        assert repo.get(b3.id) is not None


@pytest.mark.unit_test
def test_update_object():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = JobResultRepository()
        uuid = str(uuid4())
        a = JobResult(
            id=uuid,
            study_id="a",
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
        )
        b = JobResult(
            id=uuid,
            study_id="b",
            job_status=JobStatus.FAILED,
            msg="You failed !!",
            exit_code=1,
        )

        c = repo.save(a)
        d = repo.save(b)
        assert c != d
