import datetime
from unittest.mock import Mock, ANY

import pytest

from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.common.roles import RoleType
from antarest.login.model import Group, GroupDTO, Identity, UserInfo
from antarest.matrixstore.exceptions import MatrixDataSetNotFound
from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixFreq,
    Matrix,
    MatrixContent,
    MatrixDataSetUpdateDTO,
    MatrixDataSet,
    MatrixDataSetRelation,
    MatrixDataSetDTO,
    MatrixInfoDTO,
)
from antarest.matrixstore.service import MatrixService


def test_save():
    # Init Mock
    repo_content = Mock()
    repo_content.save.return_value = "my-id"

    repo = Mock()

    # Input
    dto = MatrixDTO(
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Expected
    matrix = Matrix(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=ANY,
    )

    content = MatrixContent(
        index=["1", "2"], columns=["a", "b"], data=[[1, 2]]
    )

    # Test
    service = MatrixService(
        repo=repo, repo_dataset=Mock(), content=repo_content, user_service=Mock()
    )
    id = service.create(dto)

    # Verify
    assert id == "my-id"
    repo.save.assert_called_once_with(matrix)
    repo_content.save.assert_called_once_with(content)


def test_get():
    # Init Mock
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get.return_value = Matrix(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=datetime.datetime.fromtimestamp(42),
    )

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        updated_at=101,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get("my-id")
    assert exp == res


def test_get_by_type_freq():
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get_by_freq.return_value = [
        Matrix(
            id="my-id",
            freq=MatrixFreq.WEEKLY,
            created_at=datetime.datetime.fromtimestamp(42),
        )
    ]

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        updated_at=101,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get_by_freq(freq=MatrixFreq.WEEKLY)
    assert [exp] == res
    repo.get_by_freq.assert_called_once_with(MatrixFreq.WEEKLY)


def test_delete():
    content = Mock()
    repo = Mock()
    repo_meta = Mock()

    service = MatrixService(repo, repo_meta, content, Mock())
    service.delete("my-id")
    content.delete.assert_called_once_with("my-id")
    repo.delete.assert_called_once_with("my-id")


def test_dataset_lifecycle():
    content = Mock()
    repo = Mock()
    dataset_repo = Mock()
    user_service = Mock()

    service = MatrixService(repo, dataset_repo, content, user_service)

    userA = RequestParameters(
        user=JWTUser(
            id=1,
            type="users",
            impersonator=1,
            groups=[
                JWTGroup(id="groupA", name="groupA", role=RoleType.READER)
            ],
        )
    )
    userB = RequestParameters(
        user=JWTUser(
            id=2,
            type="users",
            impersonator=2,
            groups=[
                JWTGroup(id="groupB", name="groupB", role=RoleType.READER)
            ],
        )
    )
    botA = RequestParameters(
        user=JWTUser(
            id=3,
            type="bots",
            impersonator=1,
            groups=[
                JWTGroup(id="groupA", name="groupA", role=RoleType.READER)
            ],
        )
    )

    dataset_info = MatrixDataSetUpdateDTO(
        name="datasetA",
        groups=["groupA"],
        public=True,
    )
    matrices = [
        MatrixInfoDTO(
            id="m1",
            name="A",
        ),
        MatrixInfoDTO(
            id="m2",
            name="B",
        ),
    ]

    user_service.get_group.return_value = Group(id="groupA", name="groupA")
    expected = MatrixDataSet(
        name=dataset_info.name,
        public=dataset_info.public,
        owner_id=userA.user.id,
        groups=["groupA"],
        created_at=ANY,
        updated_at=ANY,
        matrices=[
            MatrixDataSetRelation(name="A", matrix_id="m1"),
            MatrixDataSetRelation(name="B", matrix_id="m2"),
        ],
    )
    service.create_dataset(dataset_info, matrices, params=userA)
    dataset_repo.save.assert_called_with(expected)

    somedate = datetime.datetime.now()
    dataset_repo.query.return_value = [
        MatrixDataSet(
            id="some id",
            name="datasetA",
            public=True,
            owner_id=userA.user.id,
            owner=Identity(id=userA.user.id, name="userA", type="users"),
            groups=[Group(id="groupA", name="groupA")],
            created_at=somedate,
            updated_at=somedate,
            matrices=[
                MatrixDataSetRelation(name="A", matrix=Matrix(id="m1")),
                MatrixDataSetRelation(name="B", matrix=Matrix(id="m2")),
            ],
        ),
        MatrixDataSet(
            id="some id 2",
            name="datasetB",
            public=False,
            owner_id=userB.user.id,
            owner=Identity(id=userB.user.id, name="userB", type="users"),
            groups=[Group(id="groupB", name="groupB")],
            created_at=somedate,
            updated_at=somedate,
            matrices=[
                MatrixDataSetRelation(name="A", matrix=Matrix(id="m1")),
                MatrixDataSetRelation(name="B", matrix=Matrix(id="m2")),
            ],
        ),
    ]
    res = service.list("dataset", True, botA)
    dataset_repo.query.assert_called_with("dataset", botA.user.impersonator)
    assert len(res) == 1
    assert res[0] == MatrixDataSetDTO(
        id="some id",
        name="datasetA",
        public=True,
        owner=UserInfo(id=userA.user.id, name="userA"),
        groups=[GroupDTO(id="groupA", name="groupA")],
        created_at=somedate,
        updated_at=somedate,
        matrices=[
            MatrixInfoDTO(name="A", id="m1"),
            MatrixInfoDTO(name="B", id="m2"),
        ],
    )
    service.list("dataset", False, botA)
    dataset_repo.query.assert_called_with("dataset", None)
    res = service.list("dataset", False, userB)
    assert len(res) == 2

    with pytest.raises(MatrixDataSetNotFound):
        dataset_repo.get.return_value = None
        service.update_dataset(
            "dataset_id",
            MatrixDataSetUpdateDTO(
                name="datasetA",
                groups=["groupA"],
                public=True,
            ),
            userA,
        )

    dataset_repo.get.return_value = MatrixDataSet(
        id="some id",
        name="datasetA",
        public=True,
        owner_id=userA.user.id,
        owner=Identity(id=userA.user.id, name="userA", type="users"),
        groups=[Group(id="groupA", name="groupA")],
        created_at=somedate,
        updated_at=somedate,
        matrices=[
            MatrixDataSetRelation(name="A", matrix=Matrix(id="m1")),
            MatrixDataSetRelation(name="B", matrix=Matrix(id="m2")),
        ],
    )
    with pytest.raises(UserHasNotPermissionError):
        service.update_dataset(
            "dataset_id",
            MatrixDataSetUpdateDTO(
                name="datasetA",
                groups=["groupA"],
                public=True,
            ),
            userB,
        )

    user_service.get_group.return_value = Group(id="groupB", name="groupB")
    service.update_dataset(
        "some id",
        MatrixDataSetUpdateDTO(
            name="datasetA bis",
            groups=["groupB"],
            public=False,
        ),
        botA,
    )
    user_service.get_group.assert_called_with("groupB", botA)
    dataset_repo.save.assert_called_with(
        MatrixDataSet(
            id="some id",
            name="datasetA bis",
            public=False,
            groups=[Group(id="groupB", name="groupB")],
            updated_at=ANY,
        )
    )

    service.delete_dataset("dataset")
    dataset_repo.delete.assert_called_once()
