import re
import uuid

from sqlalchemy.orm.session import Session  # type: ignore

from antarest.launcher.model import JobLog, JobLogType, JobResult, JobStatus, LogType
from antarest.login.model import Identity


class TestLogType:
    def test_from_filename(self) -> None:
        """
        Test the `from_filename` method of `LogType`.
        """
        assert LogType.from_filename("antares-err.log") == LogType.STDERR
        assert LogType.from_filename("antares-out.log") == LogType.STDOUT
        assert LogType.from_filename("antares-xxx.log") is None

    def test_to_suffix(self) -> None:
        """
        Test the `to_suffix` method of `LogType`.
        """
        assert LogType.STDERR.to_suffix() == "err.log"
        assert LogType.STDOUT.to_suffix() == "out.log"


class TestJobResult:
    def test_create(self, db_session: Session) -> None:
        """
        Test the creation of a `JobResult` instance in the database.
        """
        job_result_id = str(uuid.uuid4())
        study_id = str(uuid.uuid4())
        with db_session as db:
            job_result = JobResult(
                id=job_result_id,
                study_id=study_id,
                job_status=JobStatus.RUNNING,
                msg="Running",
                exit_code=0,
            )
            db.add(job_result)
            db.commit()

        with db_session as db:
            jr = db.query(JobResult).one()
            assert jr.id == job_result_id
            assert jr.study_id == study_id
            assert jr.launcher is None
            assert jr.launcher_params is None
            assert jr.job_status is JobStatus.RUNNING
            assert jr.creation_date is not None
            assert jr.completion_date is None
            assert jr.msg == "Running"
            assert jr.output_id is None
            assert jr.exit_code == 0
            assert jr.solver_stats is None
            assert jr.logs == []
            assert jr.owner_id is None
            assert re.match(rf"Job\s*result\s+#{jr.id}", str(jr), flags=re.I)
            assert re.fullmatch(rf"<JobResult\(id='{jr.id}'.*\)>", repr(jr), flags=re.I)

    def test_create_with_owner(self, db_session: Session) -> None:
        """
        Test the creation of a `JobResult` instance associated with an owner in the database.
        """
        with db_session as db:
            identity = Identity()
            db.add(identity)
            db.commit()
            owner_id = identity.id

            job_result = JobResult(id=str(uuid.uuid4()), owner_id=owner_id)
            db.add(job_result)
            db.commit()
            job_result_id = job_result.id

        with db_session as db:
            jr = db.get(JobResult, job_result_id)
            assert jr.owner_id == owner_id

    def test_update_with_owner(self, db_session: Session) -> None:
        """
        Test the update of a `JobResult` instance with an owner in the database.
        """
        with db_session as db:
            # Create a job result without owner
            job_result = JobResult(id=str(uuid.uuid4()))
            db.add(job_result)
            db.commit()
            job_result_id = job_result.id

        with db_session as db:
            # Create an owner identity
            identity = Identity()
            db.add(identity)
            db.commit()
            owner_id = identity.id

        with db_session as db:
            # Update the job result with the owner
            job_result = db.get(JobResult, job_result_id)
            job_result.owner_id = owner_id
            db.commit()

        with db_session as db:
            jr = db.get(JobResult, job_result_id)
            assert jr.owner_id == owner_id

    def test_delete_with_owner(self, db_session: Session) -> None:
        """
        Test the deletion of an owner and check if the associated `JobResult`'s `owner_id` is set to None.
        """
        with db_session as db:
            identity = Identity()
            db.add(identity)
            db.commit()
            owner_id = identity.id

            job_result = JobResult(id=str(uuid.uuid4()), owner_id=owner_id)
            db.add(job_result)
            db.commit()
            job_result_id = job_result.id

        with db_session as db:
            identity = db.get(Identity, owner_id)
            db.delete(identity)
            db.commit()

        with db_session as db:
            # check `ondelete="SET NULL"`
            jr = db.get(JobResult, job_result_id)
            assert jr.owner_id is None


class TestJobLog:
    def test_create(self, db_session: Session) -> None:
        """
        Test the creation of a `JobResult` instance in the database.
        """
        job_result_id = str(uuid.uuid4())
        study_id = str(uuid.uuid4())
        with db_session as db:
            job_result = JobResult(
                id=job_result_id,
                study_id=study_id,
                job_status=JobStatus.RUNNING,
                msg="Running",
                exit_code=0,
            )
            db.add(job_result)
            db.commit()
            job_result_id = job_result.id

            job_log = JobLog(
                message="Log message",
                job_id=job_result_id,
                log_type=JobLogType.BEFORE,
            )
            db.add(job_log)
            db.commit()

        with db_session as db:
            jl = db.query(JobLog).one()
            assert jl.id == 1
            assert jl.message == "Log message"
            assert jl.job_id == job_result_id
            assert jl.log_type == JobLogType.BEFORE
            assert re.match(rf"Job\s*log\s+#{jl.id}", str(jl), flags=re.I)
            assert re.fullmatch(rf"<JobLog\(id={jl.id}.*\)>", repr(jl), flags=re.I)

    def test_delete_job_result(self, db_session: Session) -> None:
        """
        Test the creation of a `JobResult` instance in the database.
        """
        job_result_id = str(uuid.uuid4())
        study_id = str(uuid.uuid4())
        with db_session as db:
            job_result = JobResult(
                id=job_result_id,
                study_id=study_id,
                job_status=JobStatus.RUNNING,
                msg="Running",
                exit_code=0,
            )
            db.add(job_result)
            db.commit()
            job_result_id = job_result.id

            job_log = JobLog(
                message="Log message",
                job_id=job_result_id,
                log_type=JobLogType.BEFORE,
            )
            db.add(job_log)
            db.commit()
            job_log_id = job_log.id

        with db_session as db:
            jr = db.get(JobResult, job_result_id)
            db.delete(jr)
            db.commit()

        with db_session as db:
            # check `cascade="all, delete, delete-orphan"`
            jl = db.get(JobLog, job_log_id)
            assert jl is None
