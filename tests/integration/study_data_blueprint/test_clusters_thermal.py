import json
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
            "nh3": 0.0,
            "nmvoc": 0.0,
            "nox": 3.14,
            "op1": 0.0,
            "op2": 0.0,
            "op3": 0.0,
            "op4": 0.0,
            "op5": 0.0,
            "pm10": 0.0,
            "pm2_5": 0.0,
            "pm5": 0.0,
            "so2": 0.0,
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
        expected = ThermalFormFields(
            group=all_ini_values["group"],
            name=all_ini_values["name"],
            unit_count=all_ini_values["unitcount"],
            enabled=all_ini_values["enabled"],
            nominal_capacity=all_ini_values["nominalcapacity"],
            gen_ts=TimeSeriesGenerationOption(all_ini_values["gen-ts"]),
            min_stable_power=all_ini_values["min-stable-power"],
            min_up_time=all_ini_values["min-up-time"],
            min_down_time=all_ini_values["min-down-time"],
            must_run=all_ini_values["must-run"],
            spinning=all_ini_values["spinning"],  # percent (%)
            volatility_forced=all_ini_values["volatility.forced"],
            volatility_planned=all_ini_values["volatility.planned"],
            law_forced=LawOption(all_ini_values["law.forced"]),
            law_planned=LawOption(all_ini_values["law.planned"]),
            marginal_cost=all_ini_values["marginal-cost"],
            spread_cost=all_ini_values["spread-cost"],
            fixed_cost=all_ini_values["fixed-cost"],
            startup_cost=all_ini_values["startup-cost"],
            market_bid_cost=all_ini_values["market-bid-cost"],
            co2=all_ini_values["co2"],
            nh3=all_ini_values["nh3"],
            so2=all_ini_values["so2"],
            nox=all_ini_values["nox"],
            pm2_5=all_ini_values["pm2_5"],
            pm5=all_ini_values["pm5"],
            pm10=all_ini_values["pm10"],
            nmvoc=all_ini_values["nmvoc"],
            op1=all_ini_values["op1"],
            op2=all_ini_values["op2"],
            op3=all_ini_values["op3"],
            op4=all_ini_values["op4"],
            op5=all_ini_values["op5"],
        )
        assert actual == json.loads(expected.json(by_alias=True))

    def test_set_thermal_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `set_thermal_form_values` end point"""
        area_id = "fr"
        cluster_id = "cluster 1"
        fields = ThermalFormFields(
            group="Gas",
            name="Cluster 1",
            unit_count=1,
            enabled=True,
            nominal_capacity=2,
            gen_ts=TimeSeriesGenerationOption.FORCE_GENERATION,
            min_stable_power=0,
            min_up_time=8,
            min_down_time=12,
            must_run=True,
            spinning=25,  # percent (%)
            volatility_forced=0,
            volatility_planned=0,
            law_forced=LawOption.GEOMETRIC,
            law_planned=LawOption.UNIFORM,
            marginal_cost=0,
            spread_cost=0,
            fixed_cost=0,
            startup_cost=0,
            market_bid_cost=0,
            co2=0,
            nh3=0,
            so2=0,
            nox=3.14,
            pm2_5=0,
            pm5=0,
            pm10=0,
            nmvoc=0,
            op1=0,
            op2=0,
            op3=0,
            op4=0,
            op5=0,
        )

        # update the form values
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            # NOTE: the form field names are in camelCase
            data=fields.json(by_alias=True),
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
        # In the INI file, there are only required values or non-default values.
        # noinspection SpellCheckingInspection
        expected = {
            "gen-ts": "force generation",
            "group": "Gas",
            "law.forced": "geometric",
            "min-down-time": 12,
            "min-up-time": 8,
            "must-run": True,
            "name": "Cluster 1",
            "nominalcapacity": 2.0,
            "nox": 3.14,
            "spinning": 25,
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
