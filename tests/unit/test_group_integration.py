"""Test that group registry integrates with BaseDeflate."""

import pandas as pd

from pydeflate import imf_gdp_deflate
from pydeflate.groups import _registry


class TestGroupRegistryIntegration:
    def test_default_treatment_unchanged(self, eur_df):
        """With SOURCE treatment, behavior is unchanged."""
        result = imf_gdp_deflate(
            data=eur_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_fixed_treatment(self, eur_df):
        """FIXED treatment applies GDP-weighted deflator."""
        _registry.default_treatment = "fixed"
        result = imf_gdp_deflate(
            data=eur_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_configure_group_with_members_year(self, eur_df):
        """Per-group config with membership pinning."""
        _registry.configure("EMU", treatment="fixed", members_year=2019)
        result = imf_gdp_deflate(
            data=eur_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_non_eur_unaffected_by_treatment(self, eur_df):
        """Non-group currencies are not affected by group treatment."""
        _registry.default_treatment = "fixed"
        result = imf_gdp_deflate(
            data=eur_df,
            base_year=2022,
            source_currency="USD",
            target_currency="USD",
        )
        assert result["value"].notna().all()

    def test_source_treatment_matches_no_treatment(self, eur_df):
        """Explicit SOURCE treatment should match default behavior."""
        result_default = imf_gdp_deflate(
            data=eur_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        _registry.default_treatment = "source"
        result_explicit = imf_gdp_deflate(
            data=eur_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        pd.testing.assert_frame_equal(result_default, result_explicit)
