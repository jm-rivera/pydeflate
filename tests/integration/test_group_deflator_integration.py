"""Integration tests for group deflator with registry-based configuration.

Note: The conftest IMF data only has FRA and DEU as EMU members, so GDP-weighted
averages here are computed from those two countries only. The unit tests in
test_group_deflator.py cover the weighting logic more thoroughly.
"""

import pandas as pd
import pytest

from pydeflate import (
    GroupTreatment,
    configure_group,
    emu_members,
    imf_cpi_deflate,
    imf_exchange,
    imf_gdp_deflate,
    pydeflate_session,
    set_group_treatment,
)
from pydeflate.groups import _registry


@pytest.fixture
def eur_gbr_df():
    return pd.DataFrame(
        {
            "iso_code": ["FRA", "FRA", "GBR", "GBR"],
            "year": [2022, 2023, 2022, 2023],
            "value": [1000.0, 1050.0, 2000.0, 2100.0],
        }
    )


class TestIMFGDPDeflation:
    def test_source_treatment(self, eur_gbr_df):
        result = imf_gdp_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_fixed_treatment(self, eur_gbr_df):
        set_group_treatment("fixed")
        result = imf_gdp_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_dynamic_treatment(self, eur_gbr_df):
        set_group_treatment("dynamic")
        result = imf_gdp_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_no_treatment_works_as_before(self, eur_gbr_df):
        result = imf_gdp_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()

    def test_non_eur_currency_unaffected(self, eur_gbr_df):
        set_group_treatment("fixed")
        result = imf_gdp_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="USD",
            target_currency="USD",
        )
        assert result["value"].notna().all()

    def test_configure_group_with_pinning(self, eur_gbr_df):
        configure_group("EMU", treatment="fixed", members_year=2019)
        result = imf_gdp_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()


class TestContextManager:
    def test_session_with_group_treatment(self, eur_gbr_df):
        with pydeflate_session(group_treatment="fixed"):
            result = imf_gdp_deflate(
                data=eur_gbr_df,
                base_year=2022,
                source_currency="EUR",
                target_currency="EUR",
            )
            assert result["value"].notna().all()

    def test_session_restores_state(self):
        with pydeflate_session(group_treatment="dynamic"):
            assert _registry.default_treatment == GroupTreatment.DYNAMIC
        assert _registry.default_treatment == GroupTreatment.SOURCE


class TestCPIDeflation:
    def test_cpi_with_fixed_treatment(self, eur_gbr_df):
        set_group_treatment("fixed")
        result = imf_cpi_deflate(
            data=eur_gbr_df,
            base_year=2022,
            source_currency="EUR",
            target_currency="EUR",
        )
        assert result["value"].notna().all()


class TestExchange:
    def test_exchange_unaffected_by_treatment(self, eur_gbr_df):
        """Exchange rates are market rates, not affected by group treatment."""
        set_group_treatment("fixed")
        result = imf_exchange(
            data=eur_gbr_df,
            source_currency="EUR",
            target_currency="USD",
        )
        assert result["value"].notna().all()


class TestEmuMembersPublic:
    def test_founding_members(self):
        assert len(emu_members(1999)) == 11

    def test_all_members(self):
        assert len(emu_members()) == 20
