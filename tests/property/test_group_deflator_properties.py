"""Property-based tests for group deflator operations.

These tests use Hypothesis to verify mathematical properties that should
always hold for GDP-weighted group deflators, regardless of specific input
values. This catches edge cases in weighting, membership resolution, and
numerical stability.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from pydeflate.core.group_deflator import compute_group_deflator
from pydeflate.groups import GroupTreatment, _registry
from pydeflate.groups.emu import all_members, is_member, members_for_year
from pydeflate.sources.common import enforce_pyarrow_types

settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")


# ---------- Strategies ----------

# Years where EMU membership is interesting (transitions happen)
emu_year = st.integers(min_value=1995, max_value=2030)

# Positive deflator values (realistic range)
deflator_value = st.floats(min_value=50.0, max_value=200.0)

# Positive GDP values in billions USD
gdp_value = st.floats(min_value=1.0, max_value=50000.0)

# Two-country weight split
weight_split = st.floats(min_value=0.01, max_value=0.99)


def _make_two_country_data(
    defl_a: float,
    defl_b: float,
    gdp_a: float,
    gdp_b: float,
    year: int = 2022,
) -> pd.DataFrame:
    """Build a minimal source frame with 2 EMU members + EUR aggregate."""
    records = [
        {
            "pydeflate_year": year,
            "pydeflate_entity_code": "134",
            "pydeflate_iso3": "DEU",
            "pydeflate_NGDP_D": defl_a,
            "pydeflate_EXCHANGE": 0.85,
            "pydeflate_EXCHANGE_D": 100.0,
            "pydeflate_NGDPD": gdp_a,
        },
        {
            "pydeflate_year": year,
            "pydeflate_entity_code": "250",
            "pydeflate_iso3": "FRA",
            "pydeflate_NGDP_D": defl_b,
            "pydeflate_EXCHANGE": 0.85,
            "pydeflate_EXCHANGE_D": 100.0,
            "pydeflate_NGDPD": gdp_b,
        },
        {
            "pydeflate_year": year,
            "pydeflate_entity_code": "G163",
            "pydeflate_iso3": "EUR",
            "pydeflate_NGDP_D": 999.0,  # placeholder, will be replaced
            "pydeflate_EXCHANGE": 0.85,
            "pydeflate_EXCHANGE_D": 100.0,
            "pydeflate_NGDPD": None,
        },
    ]
    return enforce_pyarrow_types(pd.DataFrame.from_records(records))


# ---------- EMU membership properties ----------


class TestEMUMembershipProperties:
    @given(year=emu_year)
    def test_membership_is_monotonically_non_decreasing(self, year):
        """Property: members(year) is a subset of members(year+1)."""
        current = set(members_for_year(year))
        next_year = set(members_for_year(year + 1))
        assert current <= next_year

    @given(year=emu_year)
    def test_membership_count_bounded(self, year):
        """Property: member count is between 0 and total ever-members."""
        members = members_for_year(year)
        assert 0 <= len(members) <= len(all_members())

    @given(year=st.integers(min_value=2023, max_value=2100))
    def test_membership_stable_after_latest_accession(self, year):
        """Property: membership is stable after the latest accession (2023)."""
        assert members_for_year(year) == members_for_year(2023)

    @given(year=st.integers(min_value=1900, max_value=1998))
    def test_no_members_before_1999(self, year):
        """Property: no EMU members before 1999."""
        assert members_for_year(year) == []

    @given(year=emu_year)
    def test_is_member_consistent_with_members_for_year(self, year):
        """Property: is_member and members_for_year agree."""
        members = members_for_year(year)
        for iso3 in all_members():
            assert is_member(iso3, year) == (iso3 in members)


# ---------- GDP-weighted average properties ----------


class TestWeightedAverageProperties:
    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        gdp_a=gdp_value,
        gdp_b=gdp_value,
    )
    def test_weighted_average_bounded_by_inputs(
        self, defl_a, defl_b, gdp_a, gdp_b
    ):
        """Property: weighted average is between min and max of inputs."""
        data = _make_two_country_data(defl_a, defl_b, gdp_a, gdp_b)
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        weighted = eur["pydeflate_NGDP_D"].iloc[0]

        lo = min(defl_a, defl_b)
        hi = max(defl_a, defl_b)
        assert lo - 0.01 <= weighted <= hi + 0.01

    @given(
        defl=deflator_value,
        gdp_a=gdp_value,
        gdp_b=gdp_value,
    )
    def test_equal_deflators_produce_same_output(self, defl, gdp_a, gdp_b):
        """Property: if all members have the same deflator, output equals it."""
        data = _make_two_country_data(defl, defl, gdp_a, gdp_b)
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        assert abs(eur["pydeflate_NGDP_D"].iloc[0] - defl) < 0.01

    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        gdp=gdp_value,
    )
    def test_equal_gdp_produces_simple_average(self, defl_a, defl_b, gdp):
        """Property: equal GDP weights produce arithmetic mean."""
        data = _make_two_country_data(defl_a, defl_b, gdp, gdp)
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        expected = (defl_a + defl_b) / 2.0
        assert abs(eur["pydeflate_NGDP_D"].iloc[0] - expected) < 0.01

    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        w=weight_split,
    )
    def test_weight_formula_correctness(self, defl_a, defl_b, w):
        """Property: result matches the manual weighted-average formula."""
        # Use weight_split to derive GDP values that produce known weights
        total_gdp = 10000.0
        gdp_a = total_gdp * w
        gdp_b = total_gdp * (1 - w)

        data = _make_two_country_data(defl_a, defl_b, gdp_a, gdp_b)
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]

        expected = w * defl_a + (1 - w) * defl_b
        assert abs(eur["pydeflate_NGDP_D"].iloc[0] - expected) < 0.01

    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        gdp_a=gdp_value,
        gdp_b=gdp_value,
    )
    def test_non_group_rows_invariant(self, defl_a, defl_b, gdp_a, gdp_b):
        """Property: non-group rows are never modified."""
        data = _make_two_country_data(defl_a, defl_b, gdp_a, gdp_b)

        # Add a non-member row
        extra = enforce_pyarrow_types(
            pd.DataFrame(
                [
                    {
                        "pydeflate_year": 2022,
                        "pydeflate_entity_code": "001",
                        "pydeflate_iso3": "USA",
                        "pydeflate_NGDP_D": 105.0,
                        "pydeflate_EXCHANGE": 1.0,
                        "pydeflate_EXCHANGE_D": 100.0,
                        "pydeflate_NGDPD": 25000.0,
                    }
                ]
            )
        )
        data = pd.concat([data, extra], ignore_index=True)

        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        usa = result[result["pydeflate_iso3"] == "USA"]
        assert usa["pydeflate_NGDP_D"].iloc[0] == 105.0

    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        gdp_a=gdp_value,
        gdp_b=gdp_value,
    )
    def test_exchange_rate_never_modified(self, defl_a, defl_b, gdp_a, gdp_b):
        """Property: exchange rates are never touched by group deflator."""
        data = _make_two_country_data(defl_a, defl_b, gdp_a, gdp_b)
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        assert eur["pydeflate_EXCHANGE"].iloc[0] == 0.85
        assert eur["pydeflate_EXCHANGE_D"].iloc[0] == 100.0


# ---------- Treatment mode properties ----------


class TestTreatmentModeProperties:
    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        gdp_a=gdp_value,
        gdp_b=gdp_value,
    )
    def test_fixed_and_dynamic_agree_after_all_accessions(
        self, defl_a, defl_b, gdp_a, gdp_b
    ):
        """Property: for years after all accessions, fixed == dynamic."""
        # Use year 2025, well after the last accession (2023)
        data = _make_two_country_data(defl_a, defl_b, gdp_a, gdp_b, year=2025)

        result_fixed = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        result_dynamic = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=True,
        )

        eur_fixed = result_fixed[result_fixed["pydeflate_iso3"] == "EUR"]
        eur_dynamic = result_dynamic[result_dynamic["pydeflate_iso3"] == "EUR"]

        assert abs(
            eur_fixed["pydeflate_NGDP_D"].iloc[0]
            - eur_dynamic["pydeflate_NGDP_D"].iloc[0]
        ) < 0.01

    @given(
        defl_a=deflator_value,
        defl_b=deflator_value,
        gdp_a=gdp_value,
        gdp_b=gdp_value,
        pin_year=st.integers(min_value=2000, max_value=2030),
    )
    def test_pin_year_is_idempotent(
        self, defl_a, defl_b, gdp_a, gdp_b, pin_year
    ):
        """Property: applying pin_year twice gives the same result."""
        data = _make_two_country_data(defl_a, defl_b, gdp_a, gdp_b)

        result1 = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=True,
            pin_year=pin_year,
        )
        result2 = compute_group_deflator(
            result1,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=True,
            pin_year=pin_year,
        )

        eur1 = result1[result1["pydeflate_iso3"] == "EUR"]["pydeflate_NGDP_D"].iloc[0]
        eur2 = result2[result2["pydeflate_iso3"] == "EUR"]["pydeflate_NGDP_D"].iloc[0]
        assert abs(eur1 - eur2) < 0.01


# ---------- Registry properties ----------


class TestRegistryProperties:
    @pytest.fixture(autouse=True)
    def reset_registry(self):
        yield
        _registry.reset()

    def test_snapshot_restore_is_identity(self):
        """Property: snapshot then restore leaves registry unchanged."""
        _registry.default_treatment = "fixed"
        _registry.configure("EMU", treatment="dynamic", members_year=2019)

        state = _registry.snapshot()
        # Mutate
        _registry.default_treatment = "source"
        _registry.configure("EMU", treatment="source")
        # Restore
        _registry.restore(state)

        assert _registry.default_treatment == GroupTreatment.FIXED
        config = _registry.get_config("EMU")
        assert config.treatment == GroupTreatment.DYNAMIC
        assert config.members_year == 2019

    @given(treatment=st.sampled_from(["source", "fixed", "dynamic"]))
    def test_reset_always_returns_to_source(self, treatment):
        """Property: reset always returns to SOURCE regardless of prior state."""
        _registry.default_treatment = treatment
        _registry.reset()
        assert _registry.default_treatment == GroupTreatment.SOURCE

    @given(treatment=st.sampled_from(["source", "fixed", "dynamic"]))
    def test_default_treatment_roundtrip(self, treatment):
        """Property: setting then reading treatment returns same value."""
        _registry.default_treatment = treatment
        assert _registry.default_treatment == GroupTreatment(treatment)
        _registry.reset()
