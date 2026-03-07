"""Test group treatment integration with pydeflate_session."""

from pydeflate import imf_gdp_deflate, pydeflate_session
from pydeflate.groups import GroupTreatment, _registry


class TestGroupTreatmentContext:
    def test_session_sets_treatment(self, eur_df):
        with pydeflate_session(group_treatment="fixed"):
            assert _registry.default_treatment == GroupTreatment.FIXED
            result = imf_gdp_deflate(
                data=eur_df,
                base_year=2022,
                source_currency="EUR",
                target_currency="EUR",
            )
            assert result["value"].notna().all()

    def test_session_restores_treatment(self):
        assert _registry.default_treatment == GroupTreatment.SOURCE
        with pydeflate_session(group_treatment="dynamic"):
            assert _registry.default_treatment == GroupTreatment.DYNAMIC
        assert _registry.default_treatment == GroupTreatment.SOURCE

    def test_session_restores_per_group_configs(self):
        with pydeflate_session(group_treatment="fixed"):
            _registry.configure("EMU", treatment="dynamic", members_year=2019)
            config = _registry.get_config("EMU")
            assert config.members_year == 2019
        # After context, per-group config should be restored
        config = _registry.get_config("EMU")
        assert config.members_year is None
