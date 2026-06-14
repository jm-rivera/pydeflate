"""Regression tests for entity name mappings to ISO3 codes.

Tests verify that Euro area entity names map to EMU, and European Union
entities map to EU — they are distinct, not conflated.
"""

import pandas as pd
import pytest

from pydeflate.sources.common import add_pydeflate_iso3


class TestEuroAreaMapping:
    """Tests for Euro area entity name mapping to EMU ISO3 code."""

    def test_euro_area_maps_to_emu_iso3(self):
        """Euro area entity name should map to EMU ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": ["Euro area"],
                "entity_code": [998],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EMU"

    def test_euro_area_ea_with_parentheses_maps_to_emu_iso3(self):
        """'Euro Area (EA)' (actual IMF format) maps to EMU."""
        df = pd.DataFrame(
            {
                "entity": ["Euro Area (EA)"],
                "entity_code": ["G163"],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EMU"

    @pytest.mark.parametrize(
        "entity_name",
        [
            "Euro area",
            "Euro Area (EA)",
        ],
    )
    def test_euro_area_variants_map_to_emu(self, entity_name):
        """All Euro area name variants should map to EMU ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": [entity_name],
                "entity_code": ["G163"],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EMU"


class TestEuropeanUnionMapping:
    """Tests for European Union entity name mapping to EUR ISO3 code."""

    def test_european_union_maps_to_eur_iso3(self):
        """European Union entity name should map to EUR ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": ["European Union"],
                "entity_code": [998],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EU"

    def test_european_union_eu_with_parentheses_maps_to_eu_iso3(self):
        """'European Union (EU)' (actual IMF format) maps to EU."""
        df = pd.DataFrame(
            {
                "entity": ["European Union (EU)"],
                "entity_code": ["G998"],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EU"

    def test_euro_area_and_eu_are_distinct(self):
        """Euro area (EMU) and European Union (EUR) should map to different codes."""
        df = pd.DataFrame(
            {
                "entity": ["Euro area", "European Union"],
                "entity_code": ["G163", "G998"],
                "year": [2022, 2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EMU"
        assert result["pydeflate_iso3"].iloc[1] == "EU"


class TestKosovoMapping:
    """Tests for Kosovo entity name variants mapping to XXK ISO3 code."""

    @pytest.mark.parametrize(
        "entity_name",
        [
            "Kosovo",
            "Kosovo, Republic of",
        ],
    )
    def test_kosovo_variants_map_to_xxk_iso3(self, entity_name):
        """All Kosovo name variants should map to XXK ISO3 code."""
        df = pd.DataFrame(
            {
                "entity": [entity_name],
                "entity_code": ["KOS"],
                "year": [2022],
            }
        )

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "XXK"


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

        result = add_pydeflate_iso3(df, column="entity")

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

        result = add_pydeflate_iso3(df, column="entity")

        assert result["pydeflate_iso3"].iloc[0] == "EUI"
