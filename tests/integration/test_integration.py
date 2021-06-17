import time

from fastapi import FastAPI
from starlette.testclient import TestClient


def test_main(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)

    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    # check default study presence
    study_count = 0
    countdown = 10
    while study_count == 0 or countdown > 0:
        res = client.get(
            "/v1/studies",
            headers={
                "Authorization": f'Bearer {admin_credentials["access_token"]}'
            },
        )
        time.sleep(1)
        study_count = len(res.json())
        countdown -= 1

    # create some new users
    # TODO check for bad username or empty password
    client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "George", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Fred", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Harry", "password": "mypass"},
    )
    res = client.get(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 4

    # reject user with existing name creation
    res = client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "George", "password": "mypass"},
    )
    assert res.status_code == 400

    # login with new user
    # TODO mock ldap connector and test user login
    res = client.post(
        "/v1/login", json={"username": "George", "password": "mypass"}
    )
    george_credentials = res.json()
    res = client.post(
        "/v1/login", json={"username": "Fred", "password": "mypass"}
    )
    fred_credentials = res.json()
    res = client.post(
        "/v1/login", json={"username": "Harry", "password": "mypass"}
    )
    harry_credentials = res.json()

    # reject user creation from non admin
    res = client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
        json={"name": "Fred", "password": "mypass"},
    )
    assert res.status_code == 403

    # check study listing
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 1

    # study creation
    created = client.post(
        "/v1/studies/foo",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2

    # Study copy
    copied = client.post(
        f"/v1{created.json()}/copy?dest=copied",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )

    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 3

    # Study delete
    client.delete(
        f"/v1{copied.json()}",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )

    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2

    # check study permission
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 1

    # play with groups
    res = client.post(
        "/v1/groups",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Weasley"},
    )
    res = client.get(
        "/v1/groups",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    group_id = res.json()[1]["id"]
    res = client.post(
        "/v1/roles",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"type": 40, "group_id": group_id, "identity_id": 3},
    )
    res = client.post(
        "/v1/roles",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"type": 20, "group_id": group_id, "identity_id": 2},
    )
    # reset login to update credentials
    res = client.post(
        "/v1/refresh",
        headers={
            "Authorization": f'Bearer {george_credentials["refresh_token"]}'
        },
    )
    george_credentials = res.json()
    res = client.post(
        "/v1/refresh",
        headers={
            "Authorization": f'Bearer {fred_credentials["refresh_token"]}'
        },
    )
    fred_credentials = res.json()
    res = client.post(
        f"/v1/studies/bar?groups={group_id}",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 3
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2

    # running studies
    # TODO use a local launcher mock instead of using a local launcher with launcher_mock.sh (doesn't work..)
    studies = [
        study_id
        for study_id in res.json()
        if res.json()[study_id]["antares"]["caption"] == "STA-mini"
    ]
    study_id = studies[0]
    res = client.post(
        f"/v1/launcher/run/{study_id}",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    job_id = res.json()["job_id"]
    res = client.get(
        f"/v1/launcher/jobs?study_id={study_id}",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert res.json()[0]["id"] == job_id
