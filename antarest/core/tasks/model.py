import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Mapping, Optional

from pydantic import BaseModel, Extra
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Sequence, String  # type: ignore
from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.orm import Session, relationship, sessionmaker  # type: ignore

from antarest.core.persistence import Base


class TaskType(str, Enum):
    EXPORT = "EXPORT"
    VARIANT_GENERATION = "VARIANT_GENERATION"
    COPY = "COPY"
    ARCHIVE = "ARCHIVE"
    UNARCHIVE = "UNARCHIVE"
    SCAN = "SCAN"
    WORKER_TASK = "WORKER_TASK"
    UPGRADE_STUDY = "UPGRADE_STUDY"


class TaskStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    TIMEOUT = 5
    CANCELLED = 6

    def is_final(self) -> bool:
        return self in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        ]


class TaskResult(BaseModel, extra=Extra.forbid):
    success: bool
    message: str
    # Can be used to store json serialized result
    return_value: Optional[str]


class TaskLogDTO(BaseModel, extra=Extra.forbid):
    id: str
    message: str


class CustomTaskEventMessages(BaseModel, extra=Extra.forbid):
    start: str
    running: str
    end: str


class TaskEventPayload(BaseModel, extra=Extra.forbid):
    id: str
    message: str


class TaskDTO(BaseModel, extra=Extra.forbid):
    id: str
    name: str
    owner: Optional[int]
    status: TaskStatus
    creation_date_utc: str
    completion_date_utc: Optional[str]
    result: Optional[TaskResult]
    logs: Optional[List[TaskLogDTO]]
    type: Optional[str] = None
    ref_id: Optional[str] = None


class TaskListFilter(BaseModel, extra=Extra.forbid):
    status: List[TaskStatus] = []
    name: Optional[str] = None
    type: List[TaskType] = []
    ref_id: Optional[str] = None
    from_creation_date_utc: Optional[float] = None
    to_creation_date_utc: Optional[float] = None
    from_completion_date_utc: Optional[float] = None
    to_completion_date_utc: Optional[float] = None


class TaskJobLog(Base):  # type: ignore
    __tablename__ = "taskjoblog"

    id = Column(Integer(), Sequence("tasklog_id_sequence"), primary_key=True)
    message = Column(String, nullable=False)
    task_id = Column(
        String(),
        ForeignKey("taskjob.id", name="fk_log_taskjob_id"),
    )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TaskJobLog):
            return False
        return bool(other.id == self.id and other.message == self.message and other.task_id == self.task_id)

    def __repr__(self) -> str:
        return f"id={self.id}, message={self.message}, task_id={self.task_id}"

    def to_dto(self) -> TaskLogDTO:
        return TaskLogDTO(id=self.id, message=self.message)


class TaskJob(Base):  # type: ignore
    __tablename__ = "taskjob"

    id = Column(String(), default=lambda: str(uuid.uuid4()), primary_key=True)
    name = Column(String())
    status = Column(Integer(), default=lambda: TaskStatus.PENDING.value)
    creation_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime, nullable=True)
    result_msg = Column(String(), nullable=True)
    result = Column(String(), nullable=True)
    result_status = Column(Boolean(), nullable=True)
    logs = relationship(TaskJobLog, uselist=True, cascade="all, delete, delete-orphan")
    # this is not a foreign key to prevent the need to delete the job history if the user is deleted
    owner_id = Column(Integer(), nullable=True)
    type = Column(String(), nullable=True)
    ref_id = Column(String(), nullable=True)

    def to_dto(self, with_logs: bool = False) -> TaskDTO:
        return TaskDTO(
            id=self.id,
            owner=self.owner_id,
            creation_date_utc=str(self.creation_date),
            completion_date_utc=str(self.completion_date) if self.completion_date else None,
            name=self.name,
            status=TaskStatus(self.status),
            result=TaskResult(
                success=self.result_status,
                message=self.result_msg,
                return_value=self.result,
            )
            if self.completion_date
            else None,
            logs=sorted([log.to_dto() for log in self.logs], key=lambda l: l.id) if with_logs else None,
            type=self.type,
            ref_id=self.ref_id,
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TaskJob):
            return False
        return bool(
            other.id == self.id
            and other.owner_id == self.owner_id
            and other.creation_date == self.creation_date
            and other.completion_date == self.completion_date
            and other.name == self.name
            and other.status == self.status
            and other.result_msg == self.result_msg
            and other.result_status == self.result_status
            and other.logs == self.logs
        )

    def __repr__(self) -> str:
        return (
            f"id={self.id},"
            f" logs={self.logs},"
            f" owner_id={self.owner_id},"
            f" creation_date={self.creation_date},"
            f" completion_date={self.completion_date},"
            f" name={self.name},"
            f" status={self.status},"
            f" result_msg={self.result_msg},"
            f" result_status={self.result_status}"
        )


def cancel_orphan_tasks(engine: Engine, session_args: Mapping[str, bool]) -> None:
    """
    Cancel all tasks that are currently running or pending.

    When the web application restarts, such as after a new deployment, any pending or running tasks may be lost.
    To mitigate this, it is preferable to set these tasks to a "FAILED" status.
    This ensures that users can easily identify the tasks that were affected by the restart and take appropriate
    actions, such as restarting the tasks manually.

    Args:
        engine: The database engine (SQLAlchemy connection to SQLite or PostgreSQL).
        session_args: The session arguments (SQLAlchemy session arguments).
    """
    updated_values = {
        TaskJob.status: TaskStatus.FAILED.value,
        TaskJob.result_status: False,
        TaskJob.result_msg: "Task was interrupted due to server restart",
        TaskJob.completion_date: datetime.utcnow(),
    }
    with sessionmaker(bind=engine, **session_args)() as session:
        session.query(TaskJob).filter(TaskJob.status.in_([TaskStatus.RUNNING.value, TaskStatus.PENDING.value])).update(
            updated_values, synchronize_session=False
        )
        session.commit()
