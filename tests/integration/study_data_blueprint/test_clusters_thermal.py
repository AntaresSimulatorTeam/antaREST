import json
from http import HTTPStatus

import pytest
from antarest.study.business.thermal_management import (
    LawOption,
    ThermalFormFields,
    TimeSeriesGenerationOption,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
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
        obj_parameters = {
            "co2": 0.0,
            "enabled": True,
            "fixed_cost": 0,
            "genTs": TimeSeriesGenerationOption.FORCE_GENERATION.value,
            "group": "my-group",
            "lawForced": LawOption.GEOMETRIC.value,
            "lawPlanned": LawOption.UNIFORM.value,
            "marginal_cost": 0,
            "market_bid_cost": 0,
            "min_down_time": 12,
            "min_stable_power": 0,
            "min_up_time": 8,
            "must_run": True,
            "name": cluster_id,
            "nh3": 0.0,
            "nmvoc": 0.0,
            "nominal_capacity": 2,
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
            "spinning": 0.25,  # in range (0, 1)
            "spread_cost": 0,
            "startup_cost": 0,
            "unit_count": 1,
            "volatility_forced": 0,
            "volatility_planned": 0,
        }
        obj_commands = [
            {
                "action": CommandName.CREATE_CLUSTER.value,
                "args": {
                    "area_id": area_id,
                    "cluster_name": cluster_id,
                    "parameters": obj_parameters,
                },
            }
        ]
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj_commands,
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
            group="my-group",
            name=cluster_id,
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
            group="my-group",
            name=cluster_id,
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
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        expected = json.loads(fields.json(by_alias=True))
        assert actual == expected
