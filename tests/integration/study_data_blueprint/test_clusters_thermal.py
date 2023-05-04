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
        """Check `get_thermal_form_values` end point"""
        area_id = "fr"
        cluster_id = "cluster 1"

        # create a cluster in one area with the following parameters
        # noinspection PyArgumentList
        parameters = ThermalFormFields(
            group="my-group",
            name="my-name",
            unitCount=1,
            enabled=True,
            nominalCapacity=2,
            genTs=TimeSeriesGenerationOption.FORCE_GENERATION,
            minStablePower=0,
            minUpTime=8,
            minDownTime=12,
            mustRun=True,
            spinning=0,
            volatilityForced=0,
            volatilityPlanned=0,
            lawForced=LawOption.GEOMETRIC,
            lawPlanned=LawOption.UNIFORM,
            marginalCost=0,
            spreadCost=0,
            fixedCost=0,
            startupCost=0,
            marketBidCost=0,
            co2=0,
            nh3=0,
            so2=0,
            nox=3.14,
            pm25=0,
            pm5=0,
            pm10=0,
            nmvoc=0,
            op1=0,
            op2=0,
            op3=0,
            op4=0,
            op5=0,
        )

        obj_commands = [
            {
                "action": CommandName.CREATE_CLUSTER.value,
                "args": {
                    "area_id": area_id,
                    "cluster_name": cluster_id,
                    "parameters": parameters.dict(),
                },
            }
        ]
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj_commands,
        )
        res.raise_for_status()

        # get the form values
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "co2": 0.0,
            "enabled": True,
            "fixedCost": 0,
            "genTs": TimeSeriesGenerationOption.FORCE_GENERATION.value,
            "group": "my-group",
            "lawForced": LawOption.GEOMETRIC.value,
            "lawPlanned": LawOption.UNIFORM.value,
            "marginalCost": 0,
            "marketBidCost": 0,
            "minDownTime": 12,
            "minStablePower": 0,
            "minUpTime": 8,
            "mustRun": True,
            "name": cluster_id,
            "nh3": 0.0,
            "nmvoc": 0.0,
            "nominalCapacity": 2,
            "nox": 3.14,
            "op1": 0.0,
            "op2": 0.0,
            "op3": 0.0,
            "op4": 0.0,
            "op5": 0.0,
            "pm10": 0.0,
            "pm25": 0.0,
            "pm5": 0.0,
            "so2": 0.0,
            "spinning": 0,
            "spreadCost": 0,
            "startupCost": 0,
            "unitCount": 1,
            "volatilityForced": 0,
            "volatilityPlanned": 0,
        }
        assert actual == expected
