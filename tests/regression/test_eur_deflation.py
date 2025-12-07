"""Regression test for EUR deflation with IMF source.

Bug: Using EUR as source/target currency with IMF data caused:
    ValueError: No currency exchange data for to_='EUR'

The issue had two parts:
1. Entity name mappings didn't match actual IMF data format ("Euro Area (EA)" vs "Euro area")
2. The _create_eur_series function used wrong entity code (998 vs "G163")

This test ensures EUR currency deflation works correctly with IMF source.

Note: Tests use base_year=2022 and year=2023 to match the test fixture data (years 2021-2023).
"""

import pandas as pd

from pydeflate import imf_gdp_deflate


class TestEURDeflation:
    """Integration tests for EUR currency deflation."""

    def test_imf_deflate_with_eur_source_currency(self, mock_source_readers):
        """IMF deflation should work with EUR as source currency."""
        df = pd.DataFrame(
            {
                "country": ["FRA", "GBR", "CAN"],
                "year": [2023, 2023, 2023],
                "value": [1000.0, 2000.0, 1500.0],
            }
        )

        # This should not raise ValueError
        result = imf_gdp_deflate(
            data=df,
            base_year=2022,
            source_currency="EUR",
            target_currency="USD",
            id_column="country",
            year_column="year",
            value_column="value",
        )

        assert len(result) > 0
        assert "value" in result.columns

    def test_imf_deflate_with_eur_target_currency(self, mock_source_readers):
        """IMF deflation should work with EUR as target currency."""
        df = pd.DataFrame(
            {
                "country": ["FRA", "GBR", "CAN"],
                "year": [2023, 2023, 2023],
                "value": [1000.0, 2000.0, 1500.0],
            }
        )

        # This should not raise ValueError
        result = imf_gdp_deflate(
            data=df,
            base_year=2022,
            source_currency="USD",
            target_currency="EUR",
            id_column="country",
            year_column="year",
            value_column="value",
        )

        assert len(result) > 0
        assert "value" in result.columns

    def test_imf_deflate_with_eur_both_currencies(self, mock_source_readers):
        """IMF deflation should work with EUR as both source and target currency."""
        df = pd.DataFrame(
            {
                "country": ["FRA", "GBR", "CAN"],
                "year": [2023, 2023, 2023],
                "value": [1000.0, 2000.0, 1500.0],
            }
        )

        # This should not raise ValueError
        result = imf_gdp_deflate(
            data=df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
            id_column="country",
            year_column="year",
            value_column="value",
        )

        assert len(result) > 0
        assert "value" in result.columns

    def test_imf_deflate_eur_produces_reasonable_values(self, mock_source_readers):
        """EUR deflation should produce non-NaN values for countries."""
        df = pd.DataFrame(
            {
                "country": ["FRA"],
                "year": [2023],
                "value": [1000.0],
            }
        )

        result = imf_gdp_deflate(
            data=df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
            id_column="country",
            year_column="year",
            value_column="value",
        )

        # Value should be deflated (not NaN)
        assert result["value"].notna().all()
        # Deflated value should be different from original (assuming inflation/deflation)
        assert not (result["value"] == 1000.0).all()
