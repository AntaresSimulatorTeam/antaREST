import uuid
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from sqlalchemy import Column, String, ForeignKey, DateTime, Table, Integer  # type: ignore

from antarest.study.model import (
    Study,
)


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

    snapshot = relationship(VariantStudySnapshot, uselist=False)
    commands = relationship(
        CommandBlock,
        uselist=True,
        order_by="CommandBlock.index",
        cascade="all, delete, delete-orphan",
    )