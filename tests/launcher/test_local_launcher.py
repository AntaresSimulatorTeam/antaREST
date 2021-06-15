from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.common.config import Config
from antarest.launcher.business.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.model import JobStatus


@pytest.mark.unit_test
def test_compute():
    local_launcher = LocalLauncher(Config(), storage_service=Mock())

    uuid = uuid4()

    callback = Mock()
    local_launcher.add_statusupdate_callback(callback)

    local_launcher._compute(
        antares_solver_path="echo", study_path="Hello, World!", uuid=uuid
    )

    callback.assert_called_once_with(str(uuid), JobStatus.SUCCESS, False)
