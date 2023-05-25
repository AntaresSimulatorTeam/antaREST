from http import HTTPStatus

import pytest
from antarest.study.business.thermal_management import (
    THERMAL_PATH,
    LawOption,
    ThermalFormFields,
    TimeSeriesGenerationOption,
)
from starlette.testclient import TestClient


@pytest.mark.unit_test
class TestClustersThermal:
    """
    Test the end points related to thermal clusters.

    Those tests use the "examples/studies/STA-mini.zip" Study.
    """

    def test_get_thermal_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """
        Check `get_thermal_form_values` end point
        """
        area_id = "fr"
        cluster_id = "cluster 1"

        # Prepare a cluster in one area with the following parameters
        # noinspection SpellCheckingInspection
        all_ini_values = {
            # general configuration
            "name": "Cluster 1",  # Human-readable name
            "group": "Gas",  # e.g.: "Lignite", "Oil", "Gas"...
            "enabled": True,
            "unitcount": 2,
            "nominalcapacity": 100.000000,
            # TS generation
            "gen-ts": TimeSeriesGenerationOption.FORCE_GENERATION.value,
            # min. Stable Power
            "min-stable-power": 0,
            # min uptime / min downtime
            "min-up-time": 8,  # in range (1, 168)
            "min-down-time": 12,  # in range (1, 168)
            # must-run
            "must-run": True,
            # spinning
            "spinning": 25,  # in range (0, 100)
            # volatility
            "volatility.forced": 0.200000,
            "volatility.planned": 0.500000,
            # laws
            "law.forced": LawOption.GEOMETRIC.value,
            "law.planned": LawOption.UNIFORM.value,
            # costs
            "marginal-cost": 0,
            "spread-cost": 0,
            "fixed-cost": 0,
            "startup-cost": 0,
            "market-bid-cost": 0,
            # pollutant factors
            "co2": 0.0,
            # The study is in version 700, so the following value are not available:
            # "nh3": 0.0,
            # "nmvoc": 0.0,
            # "nox": 3.14,
            # "op1": 0.0,
            # "op2": 0.0,
            # "op3": 0.0,
            # "op4": 0.0,
            # "op5": 0.0,
            # "pm10": 0.0,
            # "pm2_5": 0.0,
            # "pm5": 0.0,
            # "so2": 0.0,
        }
        path = THERMAL_PATH.format(area=area_id, cluster=cluster_id)
        res = client.post(
            f"/v1/studies/{study_id}/raw?path={path}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            # In the INI file, there are only required values or non-default values.
            # Here we are going to ignore null values.
            json={k: v for k, v in all_ini_values.items() if v},
        )
        res.raise_for_status()

        # Get the form values from the following entry point
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        # Check that the result is OK and the returned value
        # matches the cluster parameters:
        assert res.status_code == HTTPStatus.OK, res.json()
        # NOTE: the form field names are in camelCase
        actual = res.json()
        # noinspection SpellCheckingInspection
        expected = {
            "co2": 0.0,
            "enabled": True,
            "fixedCost": 0.0,
            "genTs": "force generation",
            "group": "Gas",
            "lawForced": "geometric",
            "lawPlanned": "uniform",
            "marginalCost": 0.0,
            "marketBidCost": 0.0,
            "minDownTime": 12,
            "minStablePower": 0.0,
            "minUpTime": 8,
            "mustRun": True,
            "name": "Cluster 1",
            "nominalCapacity": 100.0,
            "spinning": 25.0,
            "spreadCost": 0.0,
            "startupCost": 0.0,
            "unitCount": 2,
            "volatilityForced": 0.2,
            "volatilityPlanned": 0.5,
        }
        assert actual == expected

    def test_set_thermal_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `set_thermal_form_values` end point"""
        area_id = "fr"
        cluster_id = "cluster 1"

        # Update some values (not all)
        obj = {
            "group": "Gas",
            "name": "Cluster 1",
            "unitCount": 1,
            "enabled": True,
            "nominalCapacity": 2.0,
            "genTs": "force generation",
            "minUpTime": 8,
            "minDownTime": 12,
            "mustRun": True,
            "spinning": 25.0,
            "lawForced": "geometric",
            "lawPlanned": "uniform",
            "co2": 500.0,
            # The study is in version 700, so the pollutant values are not available
            "nh3": None,
        }

        # update the form values
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            # NOTE: the form field names are in camelCase
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual is None

        # check the updated values
        path = THERMAL_PATH.format(area=area_id, cluster=cluster_id)
        res = client.get(
            f"/v1/studies/{study_id}/raw?path={path}&depth=1",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        # noinspection SpellCheckingInspection
        expected = {
            "group": "Gas",
            "name": "Cluster 1",
            "unitcount": 1,
            "enabled": True,
            "nominalcapacity": 2.0,
            "gen-ts": "force generation",
            "min-up-time": 8,
            "min-down-time": 12,
            "must-run": True,
            "spinning": 25.0,
            "law.forced": "geometric",
            "law.planned": "uniform",
            "co2": 500.0,
        }
        assert actual == expected

    def test_delete_area(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        """
        Given a study, when an area is deleted, all the thermal clusters must be removed.
        """
        area_id = "fr"
        cluster_id = "cluster 1"

        # First prepare a cluster in one area with the following parameters
        # noinspection SpellCheckingInspection
        all_ini_values = {
            # general configuration
            "name": cluster_id.title(),
            "group": "Gas",  # e.g.: "Lignite", "Oil", "Gas"...
            "enabled": True,
            "unitcount": 2,
            "nominalcapacity": 1200,
            "co2": 1.5,
        }
        path = THERMAL_PATH.format(area=area_id, cluster=cluster_id)
        res = client.post(
            f"/v1/studies/{study_id}/raw?path={path}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={k: v for k, v in all_ini_values.items() if v},
        )
        res.raise_for_status()

        # Then we remove the France area.
        # The deletion should remove all thermal clusters.
        res = client.delete(
            f"/v1/studies/{study_id}/areas/fr",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()

        # Check that the thermal cluster is removed
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.NOT_FOUND, res.json()
        actual = res.json()
        assert actual == {
            "description": "fr not a child of InputThermalClusters",
            "exception": "ChildNotFoundError",
        }

    def test_delete_cluster(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        """
        Given a study, when a cluster is deleted, it must be removed from the area.
        """
        area_id = "fr"
        cluster_id = "cluster 1"

        # First prepare a cluster in one area with the following parameters
        # noinspection SpellCheckingInspection
        all_ini_values = {
            # general configuration
            "name": cluster_id.title(),
            "group": "Gas",  # e.g.: "Lignite", "Oil", "Gas"...
            "enabled": True,
            "unitcount": 2,
            "nominalcapacity": 1200,
            "co2": 1.5,
        }
        path = THERMAL_PATH.format(area=area_id, cluster=cluster_id)
        res = client.post(
            f"/v1/studies/{study_id}/raw?path={path}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={k: v for k, v in all_ini_values.items() if v},
        )
        res.raise_for_status()

        # Then we remove the cluster
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual is None

        # Then that the cluster is deleted
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.NOT_FOUND, res.json()
        actual = res.json()
        assert actual == {
            "description": "Thermal cluster 'cluster 1' is not found in 'fr'",
            "exception": "ThermalClusterNotFound",
        }
