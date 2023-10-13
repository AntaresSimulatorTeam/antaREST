import http
import json
import pathlib
import shutil
from unittest.mock import ANY

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import RawStudy, Study
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR


@pytest.mark.integration_test
class TestFetchRawData:
    """
    Check the retrieval of Raw Data from Study: JSON, Text, or File Attachment.
    """

    def test_get_study(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """
        Test the `get_study` endpoint for fetching raw data from a study.

        This test retrieves raw data from a study identified by a UUID and checks
        if the returned data matches the expected data.

        The test performs the following steps:
        1. Copies the user resources in the Study directory.
        2. Uses the API to download files from the "user/folder" directory.
        3. Compares the fetched data with the expected data from disk.
        4. Uses the API to download files from the "user/unknown" directory.
        5. Checks for a 415 error when the extension of a file is unknown.
        """
        # First copy the user resources in the Study directory
        with db():
            study: RawStudy = db.session.get(Study, study_id)
            study_dir = pathlib.Path(study.path)
        headers = {"Authorization": f"Bearer {user_access_token}"}

        shutil.copytree(
            ASSETS_DIR.joinpath("user"),
            study_dir.joinpath("user"),
            dirs_exist_ok=True,
        )

        # Then, use the API to download the files from the "user/folder" directory
        user_folder_dir = study_dir.joinpath("user/folder")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir).as_posix()
            res = client.get(
                f"/v1/studies/{study_id}/raw",
                params={"path": f"/{rel_path}", "depth": 1},
                headers=headers,
            )
            res.raise_for_status()
            if file_path.suffix == ".json":
                # special case for JSON files
                actual = res.json()
                expected = json.loads(file_path.read_text(encoding="utf-8"))
            else:
                # NOTE ABOUT TEXT FILES {".txt", ".csv", ".tsv"}:
                # We need to read the file in binary mode to compare bytes,
                # because when reading in text mode, the universal newline
                # rule applies and so there are potentially differences between
                # Windows and Posix newlines. See the doc of the `open()` function.
                # The text files used in the unit tests resources may use CR+LF or LF
                # newlines on Windows, depending on the Git configuration `core.autocrlf`.
                actual = res.content
                expected = file_path.read_bytes()
            assert actual == expected

        # If the extension is unknown, we should have a "binary" content
        user_folder_dir = study_dir.joinpath("user/unknown")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            res = client.get(
                f"/v1/studies/{study_id}/raw",
                params={"path": f"/{rel_path.as_posix()}", "depth": 1},
                headers=headers,
            )
            res.raise_for_status()
            actual = res.content
            expected = file_path.read_bytes()
            assert actual == expected

        # If we ask for properties, we should have a JSON content
        rel_path = "/input/links/de/properties/fr"
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"/{rel_path}", "depth": 2},
            headers=headers,
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == {
            "asset-type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "display-comments": True,
            "filter-synthesis": "",
            "filter-year-by-year": "hourly",
            "hurdles-cost": True,
            "link-style": "plain",
            "link-width": 1,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": False,
        }

        # If we ask for a matrix, we should have a JSON content if formatted is True
        rel_path = "/input/links/de/fr"
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"/{rel_path}", "formatted": True},
            headers=headers,
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == {"index": ANY, "columns": ANY, "data": ANY}

        # If we ask for a matrix, we should have a CSV content if formatted is False
        rel_path = "/input/links/de/fr"
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"/{rel_path}", "formatted": False},
            headers=headers,
        )
        res.raise_for_status()
        actual = res.text
        actual_lines = actual.splitlines()
        first_row = [float(x) for x in actual_lines[0].split("\t")]
        assert first_row == [100000, 100000, 0.010000, 0.010000, 0, 0, 0, 0]

        # Some files can be corrupted
        user_folder_dir = study_dir.joinpath("user/bad")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            res = client.get(
                f"/v1/studies/{study_id}/raw",
                params={"path": f"/{rel_path.as_posix()}", "depth": 1},
                headers=headers,
            )
            assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

        # We can access to the configuration the classic way,
        # for instance, we can get the list of areas:
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": "/input/areas/list", "depth": 1},
            headers=headers,
        )
        res.raise_for_status()
        assert res.json() == ["DE", "ES", "FR", "IT"]

        # asserts that the GET /raw endpoint is able to read matrix containing NaN values
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=output/20201014-1427eco/economy/mc-all/areas/de/id-monthly",
            headers=headers,
        )
        assert res.status_code == 200
        assert np.isnan(res.json()["data"][0]).any()

        # asserts that the Debug view works properly
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=&depth=-1",
            headers=headers,
        )
        assert res.status_code == 200
