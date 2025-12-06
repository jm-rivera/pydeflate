"""Regression test for entity name mappings to ISO3 codes.

Bug: IMF WEO data uses "Euro area" as the entity name for code 998,
but the ISO3 mapping only had "European Union" -> "EUR", causing
EUR currency lookups to fail with:
    ValueError: No currency exchange data for to_='EUR'

Fix: Added "Euro area": "EUR" and other variant mappings to add_pydeflate_iso3().
"""

import pandas as pd
import pytest

from pydeflate.sources.common import add_pydeflate_iso3


class TestEuroAreaMapping:
    """Tests for Euro area entity name mapping to EUR ISO3 code."""

    def test_euro_area_maps_to_eur_iso3(self):
        """Euro area entity name should map to EUR ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": ["Euro area"],
                "entity_code": [998],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity", from_type="regex")

        assert result["pydeflate_iso3"].iloc[0] == "EUR"

    def test_european_union_also_maps_to_eur_iso3(self):
        """European Union entity name should still map to EUR ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": ["European Union"],
                "entity_code": [998],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity", from_type="regex")

        assert result["pydeflate_iso3"].iloc[0] == "EUR"

    def test_both_euro_names_map_consistently(self):
        """Both 'Euro area' and 'European Union' should map to same ISO3."""
        df = pd.DataFrame(
            {
                "entity": ["Euro area", "European Union"],
                "entity_code": [998, 999],
                "year": [2022, 2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity", from_type="regex")

        assert result["pydeflate_iso3"].iloc[0] == "EUR"
        assert result["pydeflate_iso3"].iloc[1] == "EUR"
        assert result["pydeflate_iso3"].iloc[0] == result["pydeflate_iso3"].iloc[1]


class TestDACEntityMapping:
    """Tests for DAC entity name variants mapping to DAC ISO3 code."""

    @pytest.mark.parametrize(
        "entity_name",
        [
            "DAC countries",
            "DAC Countries, Total",
            "Total DAC",
        ],
    )
    def test_dac_variants_map_to_dac_iso3(self, entity_name):
        """All DAC entity name variants should map to DAC ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": [entity_name],
                "entity_code": [20001],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity", from_type="regex")

        assert result["pydeflate_iso3"].iloc[0] == "DAC"

    def test_eu_institutions_maps_to_eui_iso3(self):
        """EU Institutions should map to EUI ISO3 code (used by DAC)."""
        df = pd.DataFrame(
            {
                "entity": ["EU Institutions"],
                "entity_code": [918],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity", from_type="regex")

        assert result["pydeflate_iso3"].iloc[0] == "EUI"
