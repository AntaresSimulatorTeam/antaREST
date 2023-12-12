import configparser
import datetime
import json
import logging
import re
import typing as t
import uuid
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from sqlalchemy import event  # type: ignore

from antarest.core.exceptions import VariantGenerationError
from antarest.core.interfaces.cache import CacheConstants
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Role, User
from antarest.study.model import RawStudy, Study, StudyAdditionalData
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy, VariantStudySnapshot
from antarest.study.storage.variantstudy.model.model import CommandDTO, GenerationResultInfoDTO
from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator, search_ref_study
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import with_db_context


def _create_variant(
    tmp_path: Path,
    variant_name: str,
    parent_id: str,
    updated_at: datetime.datetime,
    snapshot_created_at: t.Optional[datetime.datetime],
) -> VariantStudy:
    """
    Create a variant study with a snapshot (if snapshot_created_at is provided).
    """
    variant_dir = tmp_path.joinpath(f"some_place/{variant_name}")
    variant_dir.mkdir(parents=True, exist_ok=True)
    variant = VariantStudy(
        id=str(uuid.uuid4()),
        name=variant_name,
        updated_at=updated_at,
        parent_id=parent_id,
        path=str(variant_dir),
    )

    if snapshot_created_at:
        snapshot_dir = variant_dir.joinpath("snapshot")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "study.antares").touch()
        variant.snapshot = VariantStudySnapshot(
            id=variant.id,
            created_at=snapshot_created_at,
            last_executed_command=None,
        )

    return variant


class TestSearchRefStudy:
    """
    Test the `search_ref_study` method of the `SnapshotGenerator` class.

    We need to test several cases:

    Cases where we expect to have the root study and a list of `CommandBlock`
    for all variants in the order of the list.

    - The edge case where the list of studies is empty.
      Note: This case is unlikely, but the function should be able to handle it.

    - The case where the list of studies contains variants with or without snapshots,
      but a search is requested from scratch.

    - The case where the list of studies contains variants with obsolete snapshots, meaning that:
      - either there is no snapshot,
      - or the snapshot's creation date is earlier than the variant's last modification date.
      Note: The situation where the "snapshot/study.antares" file does not exist is not considered.

    Cases where we expect to have a different reference study than the root study
    and corresponding to a variant with an up-to-date snapshot.

    - The case where the list of studies contains two variants with up-to-date snapshots and
      where the first is older than the second.
      We expect to have a reference study corresponding to the second variant
      and a list of commands for the second variant.

    - The case where the list of studies contains two variants with up-to-date snapshots and
      where the first is more recent than the second.
      We expect to have a reference study corresponding to the first variant
      and a list of commands for both variants in order.

    - The case where the list of studies contains a variant with an up-to-date snapshot and
      corresponds to the generation of all commands for the variant.
      We expect to have an empty list of commands because the snapshot is already completely up-to-date.

    - The case where the list of studies contains a variant with an up-to-date snapshot and
      corresponds to a partial generation of commands for the variant.
      We expect to have a list of commands corresponding to the remaining commands.
    """

    def test_search_ref_study__empty_descendants(self) -> None:
        """
        Edge case where the list of studies is empty.
        We expect to have the root study and a list of `CommandBlock` for all variants
        in the order of the list.

        Note: This case is unlikely, but the function should be able to handle it.

        Given an empty list of descendants,
        When calling search_ref_study,
        Then the root study is returned as reference study,
        and an empty list of commands is returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")
        references: t.Sequence[VariantStudy] = []
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == root_study
        assert search_result.cmd_blocks == []
        assert search_result.force_regenerate is True

    def test_search_ref_study__from_scratch(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains variants with or without snapshots,
        but a search is requested from scratch.
        We expect to have the root study and a list of `CommandBlock` for all variants
        in the order of the list.

        Given a list of descendants with some variants with snapshots,
        When calling search_ref_study with the flag from_scratch=True,
        Then the root study is returned as reference study,
        and all commands of all variants are returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=1),
        )
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )
        variant3 = _create_variant(
            tmp_path,
            "variant3",
            variant2.id,
            datetime.datetime(year=2023, month=1, day=1),
            None,
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant1.snapshot.last_executed_command = variant1.commands[0].id
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id
        variant3.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant3.id,
                index=0,
                command="update_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "capacity": 1500}',
            ),
        ]

        # Check the variants
        references = [variant1, variant2, variant3]
        search_result = search_ref_study(root_study, references, from_scratch=True)
        assert search_result.ref_study == root_study
        assert search_result.cmd_blocks == [c for v in [variant1, variant2, variant3] for c in v.commands]
        assert search_result.force_regenerate is True

    def test_search_ref_study__obsolete_snapshots(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains variants with obsolete snapshots, meaning that:
          - either there is no snapshot,
          - or the snapshot's creation date is earlier than the variant's last modification date.
          Note: The situation where the "snapshot/study.antares" file does not exist is not considered.
        We expect to have the root study and a list of `CommandBlock` for all variants.

        Given a list of descendants with some variants with obsolete snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the root study is returned as reference study,
        and all commands of all variants are returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        # Variant 1 has no snapshot.
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=None,
        )
        # Variant 2 has an obsolete snapshot.
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=1),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id

        # Check the variants
        references = [variant1, variant2]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == root_study
        assert search_result.cmd_blocks == [c for v in [variant1, variant2] for c in v.commands]
        assert search_result.force_regenerate is True

    def test_search_ref_study__old_recent_snapshot(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with up-to-date snapshots and
        where the first is older than the second.
        We expect to have a reference study corresponding to the second variant
        and an empty list of commands, because the snapshot is already completely up-to-date.

        Given a list of descendants with some variants with up-to-date snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the second variant is returned as reference study, and no commands are returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        # Variant 1 has an up-to-date snapshot.
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=1),
        )
        # Variant 2 has an up-to-date snapshot, but is more recent than variant 1.
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=3),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant1.snapshot.last_executed_command = variant1.commands[0].id
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id

        # Check the variants
        references = [variant1, variant2]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant2
        assert search_result.cmd_blocks == []
        assert search_result.force_regenerate is False

    def test_search_ref_study__recent_old_snapshot(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with up-to-date snapshots and
        where the second is older than the first.
        We expect to have a reference study corresponding to the first variant
        and the list of commands of the second variant, because the first is completely up-to-date.

        Given a list of descendants with some variants with up-to-date snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the first variant is returned as reference study,
        and the commands of the second variant are returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        # Variant 1 has an up-to-date snapshot, but is more recent than variant 2.
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=3),
        )
        # Variant 2 has an up-to-date snapshot, but is older that variant 1.
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant1.snapshot.last_executed_command = variant1.commands[0].id
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id

        # Check the variants
        references = [variant1, variant2]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant2.commands
        assert search_result.force_regenerate is False

    def test_search_ref_study__one_variant_completely_uptodate(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot and
        corresponds to the generation of all commands for the variant (completely up-to-date)
        We expect to have an empty list of commands because the snapshot is already completely up-to-date.

        Given a list of descendants with some variants with up-to-date snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the variant is returned as reference study, and no commands are returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "capacity": 1500}',
            ),
        ]

        # The last executed command is the last item of the commands list.
        variant1.snapshot.last_executed_command = variant1.commands[-1].id

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == []
        assert search_result.force_regenerate is False

    def test_search_ref_study__one_variant_partially_uptodate(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot and
        corresponds to a partial generation of commands for the variant (partially up-to-date)
        We expect to have a list of commands corresponding to the remaining commands.

        Given a list of descendants with some variants with up-to-date snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the variant is returned as reference study, and the remaining commands are returned.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "capacity": 1500}',
            ),
        ]

        # The last executed command is the NOT last item of the commands list.
        variant1.snapshot.last_executed_command = variant1.commands[0].id

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant1.commands[1:]
        assert search_result.force_regenerate is False

    def test_search_ref_study__missing_last_command(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot,
        but the last executed command is missing (probably caused by a bug).
        We expect to have the list of all variant commands, so that the snapshot can be re-generated.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "capacity": 1500}',
            ),
        ]

        # The last executed command is missing.
        variant1.snapshot.last_executed_command = None

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant1.commands
        assert search_result.force_regenerate is True

    def test_search_ref_study__deleted_last_command(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot,
        but the last executed command is missing (removed).
        We expect to have the list of all variant commands, so that the snapshot can be re-generated.
        """
        root_study = Study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "capacity": 1500}',
            ),
        ]

        # The last executed command is missing.
        variant1.snapshot.last_executed_command = str(uuid.uuid4())

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant1.commands
        assert search_result.force_regenerate is True


class RegisterNotification:
    """
    Callable used to register notifications.
    """

    def __init__(self) -> None:
        self.notifications: t.MutableSequence[str] = []

    def __call__(self, notification: str) -> None:
        self.notifications.append(json.loads(notification))


class TestSnapshotGenerator:
    """
    Test the `SnapshotGenerator` class.
    """

    @pytest.fixture(name="jwt_user")
    def jwt_user_fixture(self) -> JWTUser:
        # Create a user in a "Writers" group:
        jwt_user = JWTUser(
            id=7,
            impersonator=7,
            type="users",
            groups=[JWTGroup(id="writers", name="Writers", role=RoleType.WRITER)],
        )
        # Ensure the user is in database.
        with db():
            role = Role(
                type=RoleType.WRITER,
                identity=User(id=jwt_user.id, name="john.doe"),
                group=Group(id="writers"),
            )
            db.session.add(role)
            db.session.commit()
        return jwt_user

    @pytest.fixture(name="root_study_id")
    def root_study_id_fixture(
        self,
        tmp_path: Path,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> str:
        # Prepare a RAW study in the temporary folder
        study_dir = tmp_path / "my-study"
        root_study_id = str(uuid.uuid4())
        root_study = RawStudy(
            id=root_study_id,
            workspace="default",
            path=str(study_dir),
            version="860",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            additional_data=StudyAdditionalData(author="john.doe"),
            owner_id=jwt_user.id,
        )

        # Create the study in database
        root_study = raw_study_service.create(root_study)

        # Create some outputs with a "simulation.log" file
        for output_name in ["20230802-1425eco", "20230802-1628eco"]:
            output_dir = study_dir / "output" / output_name
            output_dir.mkdir(parents=True)
            (output_dir / "simulation.log").touch()

        with db():
            # Save the root study in database
            variant_study_service.repository.save(root_study)
        return root_study_id

    @pytest.fixture(name="variant_study")
    def variant_study_fixture(
        self,
        root_study_id: str,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> VariantStudy:
        with db():
            # Create un new variant
            name = "my-variant"
            params = RequestParameters(user=jwt_user)
            variant_study = variant_study_service.create_variant_study(root_study_id, name, params=params)

            # Append some commands
            variant_study_service.append_commands(
                variant_study.id,
                [
                    CommandDTO(action="create_area", args={"area_name": "North"}),
                    CommandDTO(action="create_area", args={"area_name": "South"}),
                    CommandDTO(action="create_link", args={"area1": "north", "area2": "south"}),
                    CommandDTO(
                        action="create_cluster",
                        args={
                            "area_id": "south",
                            "cluster_name": "gas_cluster",
                            "parameters": {"group": "Gas", "unitcount": 1, "nominalcapacity": 500},
                        },
                    ),
                ],
                params=params,
            )
            return variant_study

    def test_init(self, variant_study_service: VariantStudyService) -> None:
        """
        Test the initialization of the `SnapshotGenerator` class.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )
        assert generator.cache == variant_study_service.cache
        assert generator.raw_study_service == variant_study_service.raw_study_service
        assert generator.command_factory == variant_study_service.command_factory
        assert generator.study_factory == variant_study_service.study_factory
        assert generator.patch_service == variant_study_service.patch_service
        assert generator.repository == variant_study_service.repository

    @with_db_context
    def test_generate__nominal_case(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> None:
        """
        Test the generation of a variant study based on a raw study.

        Given a raw study and a single variant study,
        When calling generate with:
        - `denormalize` set to False,
        - `from_scratch` set to False,
        - `notifier` set to a callback function used to register de notifications,
        Then the variant generation must succeed.
        We must check that:
        - the number of database queries is kept as low as possible,
        - the variant is correctly generated in the "snapshot" directory and all commands are applied,
        - the matrices are not denormalized (we should have links to matrices),
        - the variant is updated in the database (snapshot and additional_data),
        - the cache is updated with the new variant configuration,
        - the temporary directory is correctly removed.
        - the notifications are correctly registered.
        - the simulation outputs are not copied.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )

        notifier = RegisterNotification()

        with DBStatementRecorder(db.session.bind) as db_recorder:
            results = generator.generate_snapshot(
                variant_study.id,
                jwt_user,
                denormalize=False,
                from_scratch=False,
                notifier=notifier,
            )

        # Check: the number of database queries is kept as low as possible.
        # We expect 5 queries:
        # - 1 query to fetch the ancestors of a variant study,
        # - 1 query to fetch the root study (with owner and groups for permission check),
        # - 1 query to fetch the list of variants with snapshot, commands, etc.,
        # - 1 query to update the variant study additional_data,
        # - 1 query to insert the variant study snapshot.
        assert len(db_recorder.sql_statements) == 5, str(db_recorder)

        # Check: the variant generation must succeed.
        assert results == GenerationResultInfoDTO(
            success=True,
            details=[
                ("create_area", True, "Area 'North' created"),
                ("create_area", True, "Area 'South' created"),
                ("create_link", True, "Link between 'north' and 'south' created"),
                ("create_cluster", True, "Thermal cluster 'gas_cluster' added to area 'south'."),
            ],
        )

        # Check: the variant is correctly generated and all commands are applied.
        snapshot_dir = variant_study.snapshot_dir
        assert snapshot_dir.exists()
        assert (snapshot_dir / "study.antares").exists()
        assert (snapshot_dir / "input/areas/list.txt").read_text().splitlines(keepends=False) == ["North", "South"]
        config = configparser.RawConfigParser()
        config.read(snapshot_dir / "input/links/north/properties.ini")
        assert config.sections() == ["south"]
        assert config["south"], "The 'south' section must exist in the 'properties.ini' file."
        config = configparser.RawConfigParser()
        config.read(snapshot_dir / "input/thermal/clusters/south/list.ini")
        assert config.sections() == ["gas_cluster"]
        assert config["gas_cluster"] == {  # type: ignore
            "group": "Gas",
            "unitcount": "1",
            "nominalcapacity": "500",
            "name": "gas_cluster",
        }

        # Check: the matrices are not denormalized (we should have links to matrices).
        assert (snapshot_dir / "input/links/north/south_parameters.txt.link").exists()
        assert (snapshot_dir / "input/thermal/series/south/gas_cluster/series.txt.link").exists()

        # Check: the variant is updated in the database (snapshot and additional_data).
        with db():
            study = variant_study_service.repository.get(variant_study.id)
            assert study is not None
            assert study.snapshot is not None
            assert study.snapshot.last_executed_command == study.commands[-1].id
            assert study.additional_data.author == "john.doe"

        # Check: the cache is updated with the new variant configuration.
        # The cache is a mock created in the session's scope, so it is shared between all tests.
        cache: Mock = generator.cache  # type: ignore
        # So, the number of calls to the `put` method is at least equal to 2.
        assert cache.put.call_count >= 2
        # The last call to the `put` method is for the variant study.
        put_variant = cache.put.call_args_list[-1]
        assert put_variant[0][0] == f"{CacheConstants.STUDY_FACTORY}/{variant_study.id}"
        variant_study_config = put_variant[0][1]
        assert variant_study_config["study_id"] == variant_study.id

        # Check: the temporary directory is correctly removed.
        assert list(snapshot_dir.parent.iterdir()) == [snapshot_dir]

        # Check: the notifications are correctly registered.
        assert notifier.notifications == [  # type: ignore
            {
                "details": [
                    ["create_area", True, "Area 'North' created"],
                    ["create_area", True, "Area 'South' created"],
                    ["create_link", True, "Link between 'north' and 'south' created"],
                    ["create_cluster", True, "Thermal cluster 'gas_cluster' added to area 'south'."],
                ],
                "success": True,
            }
        ]

        # Check: the simulation outputs are not copied.
        assert not (snapshot_dir / "output").exists()

    @with_db_context
    def test_generate__with_user_dir(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> None:
        """
        Test the generation of a variant study containing a user directory.
        We expect that the user directory is correctly preserved.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )

        # Generate the snapshot once
        generator.generate_snapshot(
            variant_study.id,
            jwt_user,
            denormalize=False,
            from_scratch=False,
        )

        # Add a user directory to the variant study.
        user_dir = Path(variant_study.snapshot_dir) / "user"
        user_dir.mkdir(parents=True, exist_ok=True)
        user_dir.joinpath("user_file.txt").touch()

        # Generate the snapshot again
        generator.generate_snapshot(
            variant_study.id,
            jwt_user,
            denormalize=False,
            from_scratch=False,
        )

        # Check that the user directory is correctly preserved.
        user_dir = Path(variant_study.snapshot_dir) / "user"
        assert user_dir.is_dir()
        assert user_dir.joinpath("user_file.txt").exists()

    @with_db_context
    def test_generate__with_denormalize_true(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> None:
        """
        Test the generation of a variant study with matrices de-normalization.
        We expect that all matrices are correctly denormalized (no link).
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )

        results = generator.generate_snapshot(
            variant_study.id,
            jwt_user,
            denormalize=True,
            from_scratch=False,
        )

        # Check the results
        assert results == GenerationResultInfoDTO(
            success=True,
            details=[
                ("create_area", True, "Area 'North' created"),
                ("create_area", True, "Area 'South' created"),
                ("create_link", True, "Link between 'north' and 'south' created"),
                ("create_cluster", True, "Thermal cluster 'gas_cluster' added to area 'south'."),
            ],
        )

        # Check: the matrices are denormalized (we should have TSV files).
        snapshot_dir = variant_study.snapshot_dir
        assert (snapshot_dir / "input/links/north/south_parameters.txt").exists()
        array = np.loadtxt(snapshot_dir / "input/links/north/south_parameters.txt", delimiter="\t")
        assert array.shape == (8760, 6)

        assert (snapshot_dir / "input/thermal/series/south/gas_cluster/series.txt").exists()
        array = np.loadtxt(snapshot_dir / "input/thermal/series/south/gas_cluster/series.txt", delimiter="\t")
        assert array.size == 0

    @with_db_context
    def test_generate__with_invalid_command(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> None:
        """
        Test the generation of a variant study with an invalid command.
        We expect to have a clear error message explaining which command fails.
        The snapshot directory must be removed (and no temporary directory must be left).
        """
        # Append an invalid command to the variant study.
        params = RequestParameters(user=jwt_user)
        variant_study_service.append_commands(
            variant_study.id,
            [
                CommandDTO(action="create_area", args={"area_name": "North"}),  # duplicate
            ],
            params=params,
        )

        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )

        err_msg = (
            f"Failed to generate variant study {variant_study.id}:"
            f" Area 'North' already exists and could not be created"
        )
        with pytest.raises(VariantGenerationError, match=re.escape(err_msg)):
            generator.generate_snapshot(
                variant_study.id,
                jwt_user,
                denormalize=False,
                from_scratch=False,
            )

        # Check: the snapshot directory is removed.
        snapshot_dir = variant_study.snapshot_dir
        assert not snapshot_dir.exists()

        # Check: no temporary directory is left.
        assert list(snapshot_dir.parent.iterdir()) == []

    @with_db_context
    def test_generate__notification_failure(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """
        Test the generation of a variant study with a notification that fails.
        Since the notification is not critical, we expect to have no exception.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )

        notifier = Mock(side_effect=Exception("Something went wrong"))

        with caplog.at_level(logging.WARNING):
            results = generator.generate_snapshot(
                variant_study.id,
                jwt_user,
                denormalize=False,
                from_scratch=False,
                notifier=notifier,
            )

        # Check the results
        assert results == GenerationResultInfoDTO(
            success=True,
            details=[
                ("create_area", True, "Area 'North' created"),
                ("create_area", True, "Area 'South' created"),
                ("create_link", True, "Link between 'north' and 'south' created"),
                ("create_cluster", True, "Thermal cluster 'gas_cluster' added to area 'south'."),
            ],
        )

        # Check th logs
        assert "Something went wrong" in caplog.text

    @with_db_context
    def test_generate__variant_of_variant(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> None:
        """
        Test the generation of a variant study of a variant study.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )

        # Generate the variant once.
        generator.generate_snapshot(
            variant_study.id,
            jwt_user,
            denormalize=False,
            from_scratch=False,
        )

        # Create a new variant of the variant study.
        params = RequestParameters(user=jwt_user)
        new_variant = variant_study_service.create_variant_study(variant_study.id, "my-variant", params=params)

        # Append some commands to the new variant.
        variant_study_service.append_commands(
            new_variant.id,
            [
                CommandDTO(action="create_area", args={"area_name": "East"}),
            ],
            params=params,
        )

        # Generate the variant again.
        results = generator.generate_snapshot(
            new_variant.id,
            jwt_user,
            denormalize=False,
            from_scratch=False,
        )

        # Check the results
        assert results == GenerationResultInfoDTO(success=True, details=[("create_area", True, "Area 'East' created")])
