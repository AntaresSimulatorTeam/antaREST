import json
import uuid
from dataclasses import dataclass

from sqlalchemy import Column, String, ForeignKey, DateTime, Table, Integer  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from antarest.study.model import (
    Study,
    DEFAULT_WORKSPACE_NAME,
)
from antarest.study.storage.variantstudy.model import CommandDTO


@dataclass
class VariantStudySnapshot(Base):  # type: ignore
    """
    Variant Study Snapshot based entity implementation.
    """

    __tablename__ = "variant_study_snapshot"

    id = Column(
        String(36),
        ForeignKey("variantstudy.id"),
        primary_key=True,
    )
    created_at = Column(DateTime)
    path = Column(String(255))
    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }


@dataclass
class CommandBlock(Base):  # type: ignore
    """
    Command Block based entity implementation.
    """

    __tablename__ = "commandblock"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    study_id = Column(String(36), ForeignKey("variantstudy.id"))
    index = Column(Integer)
    command = Column(String(255))
    version = Column(Integer)
    args = Column(String())
    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            id=self.id, action=self.command, args=json.loads(self.args)
        )


@dataclass
class VariantStudy(Study):
    """
    Study filesystem based entity implementation.
    """

    __tablename__ = "variantstudy"

    id = Column(
        String(36),
        ForeignKey("study.id"),
        primary_key=True,
    )
    path = Column(String(255))
    __mapper_args__ = {
        "polymorphic_identity": "variantstudy",
    }
    workspace = Column(String(255), default=DEFAULT_WORKSPACE_NAME)
    snapshot = relationship(VariantStudySnapshot, uselist=False)
    commands = relationship(
        CommandBlock,
        uselist=True,
        order_by="CommandBlock.index",
        cascade="all, delete, delete-orphan",
    )
