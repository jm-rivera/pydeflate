"""Property-based tests for deflation operations.

These tests use Hypothesis to verify mathematical properties that should
always hold, regardless of specific input values. This catches edge cases
and numerical stability issues that example-based tests might miss.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

# Configure Hypothesis for reasonable test times
settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")


@pytest.fixture
def sample_deflator_data():
    """Fixture providing sample deflator data for testing."""
    from pydeflate.sources.common import enforce_pyarrow_types

    data = {
        "pydeflate_year": [2020, 2021, 2022] * 2,
        "pydeflate_entity_code": ["001", "001", "001", "250", "250", "250"],
        "pydeflate_iso3": ["USA", "USA", "USA", "FRA", "FRA", "FRA"],
        "pydeflate_NGDP_D": [95.0, 100.0, 105.0, 98.0, 100.0, 103.0],
        "pydeflate_EXCHANGE": [1.0, 1.0, 1.0, 0.85, 0.88, 0.90],
        "pydeflate_EXCHANGE_D": [98.0, 100.0, 102.0, 97.0, 100.0, 105.0],
    }
    return enforce_pyarrow_types(pd.DataFrame(data))


class TestDeflatorRebasing:
    """Test properties of deflator rebasing."""

    @given(
        base_year=st.integers(min_value=2000, max_value=2020),
        deflator_value=st.floats(min_value=50.0, max_value=200.0),
    )
    def test_rebasing_to_base_year_equals_100(self, base_year, deflator_value):
        """Property: Deflator at base year should equal 100 after rebasing."""
        from pydeflate.core.deflator import PriceDeflator
        from pydeflate.sources.common import enforce_pyarrow_types

        # Create synthetic data with known base year
        test_data = enforce_pyarrow_types(
            pd.DataFrame(
                {
                    "pydeflate_year": [base_year - 1, base_year, base_year + 1],
                    "pydeflate_entity_code": ["001"] * 3,
                    "pydeflate_iso3": ["USA"] * 3,
                    "pydeflate_NGDP_D": [
                        deflator_value * 0.95,
                        deflator_value,
                        deflator_value * 1.05,
                    ],
                }
            )
        )

        # Mock source - define class outside to avoid scope issues
        class MockSource:
            def __init__(self, data):
                self.name = "Test"
                self.data = data
                self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

            def price_deflator(self, kind):
                return self.data

        source = MockSource(test_data)
        deflator = PriceDeflator(source=source, kind="NGDP_D", base_year=base_year)

        # Get rebased data for base year
        base_year_data = deflator.deflator_data[
            deflator.deflator_data["pydeflate_year"] == base_year
        ]

        # Should have exactly one row for base year
        assert len(base_year_data) == 1

        # Deflator at base year should be exactly 100
        # Note: Column name is pydeflate_NGDP_D (already has _D suffix)
        assert abs(base_year_data["pydeflate_NGDP_D"].iloc[0] - 100.0) < 0.01

    @given(
        multiplier=st.floats(min_value=0.1, max_value=10.0),
    )
    def test_rebasing_preserves_ratios(self, multiplier):
        """Property: Rebasing preserves ratios between years."""
        from pydeflate.core.deflator import PriceDeflator
        from pydeflate.sources.common import enforce_pyarrow_types

        base_value = 100.0
        year1_value = base_value * multiplier

        test_data = enforce_pyarrow_types(
            pd.DataFrame(
                {
                    "pydeflate_year": [2020, 2021],
                    "pydeflate_entity_code": ["001", "001"],
                    "pydeflate_iso3": ["USA", "USA"],
                    "pydeflate_NGDP_D": [base_value, year1_value],
                }
            )
        )

        class MockSource:
            def __init__(self, data):
                self.name = "Test"
                self.data = data
                self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

            def price_deflator(self, kind):
                return self.data

        source = MockSource(test_data)
        deflator = PriceDeflator(source=source, kind="NGDP_D", base_year=2020)

        # Get rebased values
        rebased = deflator.deflator_data.set_index("pydeflate_year")
        # Note: Column name is pydeflate_NGDP_D (already has _D suffix)
        base_rebased = rebased.loc[2020, "pydeflate_NGDP_D"]
        year1_rebased = rebased.loc[2021, "pydeflate_NGDP_D"]

        # Ratio should be preserved (within floating point error)
        original_ratio = year1_value / base_value
        rebased_ratio = year1_rebased / base_rebased

        assert abs(original_ratio - rebased_ratio) < 0.001


class TestExchangeRateConversions:
    """Test properties of exchange rate conversions."""

    @given(
        amount=st.floats(min_value=1.0, max_value=1_000_000.0),
        usd_to_eur=st.floats(min_value=0.5, max_value=2.0),
    )
    def test_exchange_roundtrip_identity(self, amount, usd_to_eur):
        """Property: Converting A→B→A returns original value."""
        from pydeflate.core.exchange import Exchange
        from pydeflate.sources.common import enforce_pyarrow_types

        # Create exchange rate data
        data = pd.DataFrame(
            {
                "pydeflate_year": [2020],
                "pydeflate_entity_code": ["001"],
                "pydeflate_iso3": ["USA"],
                "pydeflate_EXCHANGE": [1.0],  # USD to USD
            }
        )

        # Add EUR data
        eur_data = pd.DataFrame(
            {
                "pydeflate_year": [2020],
                "pydeflate_entity_code": ["978"],
                "pydeflate_iso3": ["EUR"],
                "pydeflate_EXCHANGE": [usd_to_eur],  # EUR to USD
            }
        )

        combined = enforce_pyarrow_types(pd.concat([data, eur_data], ignore_index=True))

        class MockSource:
            name = "Test"
            data = combined
            _idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

            def lcu_usd_exchange(self):
                return self.data

        source = MockSource()

        # USD → EUR
        usd_to_eur_ex = Exchange(
            source=source, source_currency="USA", target_currency="EUR"
        )

        # EUR → USD
        eur_to_usd_ex = Exchange(
            source=source, source_currency="EUR", target_currency="USA"
        )

        # Get exchange rates
        usd_eur_rate = usd_to_eur_ex.exchange_data[
            usd_to_eur_ex.exchange_data["pydeflate_iso3"] == "USA"
        ]["pydeflate_EXCHANGE"].iloc[0]

        eur_usd_rate = eur_to_usd_ex.exchange_data[
            eur_to_usd_ex.exchange_data["pydeflate_iso3"] == "EUR"
        ]["pydeflate_EXCHANGE"].iloc[0]

        # Roundtrip should return original
        roundtrip = amount * usd_eur_rate * eur_usd_rate

        # Allow for floating point error
        assert abs(roundtrip - amount) / amount < 0.01

    @given(
        usd_to_eur=st.floats(min_value=0.5, max_value=2.0),
        usd_to_gbp=st.floats(min_value=0.5, max_value=2.0),
    )
    def test_exchange_transitivity(self, usd_to_eur, usd_to_gbp):
        """Property: A→B + B→C = A→C (triangle inequality)."""
        from pydeflate.core.exchange import Exchange
        from pydeflate.sources.common import enforce_pyarrow_types

        # Calculate derived EUR→GBP rate
        eur_to_gbp = usd_to_gbp / usd_to_eur

        data = pd.DataFrame(
            {
                "pydeflate_year": [2020, 2020, 2020],
                "pydeflate_entity_code": ["001", "978", "826"],
                "pydeflate_iso3": ["USA", "EUR", "GBR"],
                "pydeflate_EXCHANGE": [1.0, usd_to_eur, usd_to_gbp],
            }
        )

        combined = enforce_pyarrow_types(data)

        class MockSource:
            name = "Test"
            data = combined
            _idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

            def lcu_usd_exchange(self):
                return self.data

        source = MockSource()

        # EUR → GBP direct
        eur_gbp_ex = Exchange(
            source=source, source_currency="EUR", target_currency="GBR"
        )

        # Get the exchange rate
        eur_gbp_rate = eur_gbp_ex.exchange_data[
            eur_gbp_ex.exchange_data["pydeflate_iso3"] == "EUR"
        ]["pydeflate_EXCHANGE"].iloc[0]

        # Should match calculated rate
        assert abs(eur_gbp_rate - eur_to_gbp) / eur_to_gbp < 0.01


class TestDeflationOperations:
    """Test properties of deflation calculations."""

    @given(
        value=st.floats(min_value=1.0, max_value=1_000_000.0),
        deflator_current=st.floats(min_value=50.0, max_value=200.0),
        deflator_base=st.floats(min_value=50.0, max_value=200.0),
    )
    def test_deflation_then_inflation_identity(
        self, value, deflator_current, deflator_base
    ):
        """Property: Deflating then inflating returns original value."""
        # This tests the core formula: value / deflator * deflator = value

        # Deflation: convert current to constant
        deflated = value * (deflator_base / deflator_current)

        # Inflation: convert constant back to current
        inflated = deflated * (deflator_current / deflator_base)

        # Should return original (within floating point error)
        assert abs(inflated - value) / value < 1e-6

    @given(
        values=st.lists(
            st.floats(min_value=1.0, max_value=10000.0), min_size=2, max_size=10
        ),
        deflator=st.floats(min_value=0.1, max_value=10.0),
    )
    def test_deflation_preserves_sums(self, values, deflator):
        """Property: Deflating sum = sum of deflated values."""
        import numpy as np

        # Deflate sum
        total = sum(values)
        deflated_total = total / deflator

        # Sum of deflated
        deflated_values = [v / deflator for v in values]
        sum_of_deflated = sum(deflated_values)

        # Should be equal (within floating point error)
        assert abs(deflated_total - sum_of_deflated) < 1e-6

    @given(
        value=st.floats(min_value=1.0, max_value=1_000_000.0),
        deflator=st.floats(min_value=0.1, max_value=10.0),
    )
    def test_deflation_monotonicity(self, value, deflator):
        """Property: If deflator > 1, deflated value < original."""
        deflated = value / deflator

        if deflator > 1.0:
            assert deflated < value
        elif deflator < 1.0:
            assert deflated > value
        else:  # deflator == 1.0
            assert abs(deflated - value) < 1e-6


class TestDataMerging:
    """Test properties of data merging operations."""

    @given(
        n_entities=st.integers(min_value=1, max_value=20),
        n_years=st.integers(min_value=1, max_value=10),
    )
    def test_merge_preserves_user_rows(self, n_entities, n_years):
        """Property: Merging should not duplicate user data rows."""
        from pydeflate.sources.common import enforce_pyarrow_types
        from pydeflate.utils import merge_user_and_pydeflate_data

        # Create user data
        user_data = []
        for entity_id in range(n_entities):
            for year in range(2020, 2020 + n_years):
                user_data.append(
                    {
                        "entity": f"E{entity_id:03d}",
                        "pydeflate_year": year,
                        "value": 100.0,
                    }
                )

        user_df = enforce_pyarrow_types(pd.DataFrame(user_data))

        # Create pydeflate data (matching entities/years)
        pydeflate_data = []
        for entity_id in range(n_entities):
            for year in range(2020, 2020 + n_years):
                pydeflate_data.append(
                    {
                        "pydeflate_year": year,
                        "pydeflate_entity_code": f"E{entity_id:03d}",
                        "pydeflate_iso3": f"E{entity_id:03d}",
                        "pydeflate_deflator": 100.0,
                    }
                )

        pydeflate_df = enforce_pyarrow_types(pd.DataFrame(pydeflate_data))

        # Merge
        merged = merge_user_and_pydeflate_data(
            data=user_df,
            pydeflate_data=pydeflate_df,
            entity_column="entity",
            ix=["pydeflate_year", "pydeflate_iso3"],
            source_codes=False,
            dac=False,
        )

        # Count matched rows (excluding right_only)
        matched = merged[merged["_merge"] != "right_only"]

        # Should have exactly same number of rows as user data
        assert len(matched) == len(user_df)
