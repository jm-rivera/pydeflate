"""Regression test for to_current parameter bug.

This test verifies that when to_current=True, the conversion from constant prices
to current prices works correctly.

Bug description:
- When converting from constant USD to current EUR with to_current=True
- The operation was dividing by the deflator instead of multiplying
- This resulted in incorrect values (too high by approximately the square of the exchange rate)

Expected behavior:
- For base year, constant prices should equal current prices in the source currency
- Converting constant USD to current EUR should simply apply the exchange rate for base year
- For non-base years, it should account for both price changes and exchange rate changes
"""

import pandas as pd
import pytest

from pydeflate import oecd_dac_deflate, set_pydeflate_path


class TestToCurrentBug:
    """Test suite for to_current parameter bug fix."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up cache path for tests."""
        set_pydeflate_path(str(tmp_path / ".cache"))

    def test_to_current_base_year_simple_exchange(self):
        """Test that base year conversion is a simple exchange rate application.

        For the base year:
        - constant USD = current USD (base year definition)
        - current EUR = current USD * exchange_rate
        - Therefore: constant USD -> current EUR should just apply exchange rate
        """
        # Using 2023 as base year since test fixtures include data up to 2023
        data = pd.DataFrame(
            {
                "iso_code": ["FRA"],
                "year": [2023],
                "constant_usd": [1000.0],
            }
        )

        result = oecd_dac_deflate(
            data=data,
            base_year=2023,
            source_currency="USA",
            target_currency="EUR",
            id_column="iso_code",
            year_column="year",
            value_column="constant_usd",
            target_value_column="current_eur",
            to_current=True,
        )

        # Get the exchange rate from the result to calculate expected value
        # For base year, constant USD should convert to current EUR via exchange rate
        # We'll verify the mathematical relationship rather than a specific value
        actual = result["current_eur"].iloc[0]

        # The current implementation incorrectly divides, making values too high
        # With the bug, the value would be > 1000 (incorrect)
        # After fix, the value should be < 1000 (since EUR is typically < 1 USD)
        # This test will fail with current bug and pass after fix
        assert actual < 1000.0, (
            f"Base year conversion seems incorrect. Got {actual}, expected < 1000 "
            f"(since 1 USD < 1 EUR historically). This suggests division instead of multiplication."
        )

    def test_to_current_full_example(self):
        """Test conversion with multiple years using base year 2023."""
        # Using 2023 as base year and including years in test fixtures
        data = {
            "iso_code": ["FRA", "FRA", "FRA"],
            "year": [2023, 2022, 2021],
            "constant_usd": [1000.0, 1000.0, 1000.0],
        }

        df = pd.DataFrame(data)

        result = oecd_dac_deflate(
            data=df,
            base_year=2023,
            source_currency="USA",
            target_currency="EUR",
            id_column="iso_code",
            year_column="year",
            value_column="constant_usd",
            target_value_column="current_eur",
            to_current=True,
        )

        # For all years, values should be less than source value
        # since EUR < USD historically
        for idx, row in result.iterrows():
            year = row["year"]
            actual = row["current_eur"]

            assert actual < 1000.0, (
                f"Year {year} conversion seems incorrect. Got {actual}, expected < 1000. "
                f"This suggests division instead of multiplication by exchange rate."
            )

    def test_to_current_inverse_of_to_constant(self):
        """Test that to_current=True is the inverse of to_current=False.

        If we convert constant -> current -> constant, we should get back the original.
        """
        data = pd.DataFrame(
            {
                "iso_code": ["FRA", "FRA", "FRA"],
                "year": [2023, 2022, 2021],
                "constant_usd": [1000.0, 1000.0, 1000.0],
            }
        )

        # Step 1: Convert constant USD to current USD (should be identity for same currency)
        current = oecd_dac_deflate(
            data=data,
            base_year=2023,
            source_currency="USA",
            target_currency="USA",
            id_column="iso_code",
            year_column="year",
            value_column="constant_usd",
            target_value_column="current_usd",
            to_current=True,
        )

        # Step 2: Convert current USD back to constant USD
        roundtrip = oecd_dac_deflate(
            data=current,
            base_year=2023,
            source_currency="USA",
            target_currency="USA",
            id_column="iso_code",
            year_column="year",
            value_column="current_usd",
            target_value_column="constant_usd_roundtrip",
            to_current=False,
        )

        # The roundtrip should give us back the original constant values
        for idx in roundtrip.index:
            year = roundtrip.loc[idx, "year"]
            original = data.loc[data["year"] == year, "constant_usd"].values[0]
            roundtrip_val = roundtrip.loc[idx, "constant_usd_roundtrip"]

            # Allow 0.1% tolerance for rounding errors
            assert abs(roundtrip_val - original) / original < 0.001, (
                f"Year {year} roundtrip failed. Original: {original}, Roundtrip: {roundtrip_val}"
            )
