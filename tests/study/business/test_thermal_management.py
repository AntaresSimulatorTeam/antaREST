from antarest.study.business.thermal_management import (
    LawOption,
    ThermalFormFields,
    TimeSeriesGenerationOption,
)


class TestThermalFormFields:
    def test_thermal_form_fields__aliases(self):
        """
        This test builds a `ThermalFormFields` object and then converts it to
        a Python dictionary using aliases to verify that the aliases
        are in "camelCase" format.
        """
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
            spinning=25,
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
        actual = fields.dict(by_alias=True)
        expected = dict(
            group="Gas",
            name="Cluster 1",
            unitCount=1,
            enabled=True,
            nominalCapacity=2,
            genTs=TimeSeriesGenerationOption.FORCE_GENERATION,
            minStablePower=0,
            minUpTime=8,
            minDownTime=12,
            mustRun=True,
            spinning=25,
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
        assert actual == expected
