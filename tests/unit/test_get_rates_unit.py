import pandas as pd
import pytest

from pydeflate import (
    get_imf_exchange_rates,
    get_oecd_dac_exchange_rates,
    get_wb_exchange_rates,
    get_wb_ppp_rates,
)


def test_get_exchange_rates_returns_dataframe(sample_source_frames):
    """Test that get_exchange_rates returns a DataFrame with expected columns."""
    result = get_imf_exchange_rates()

    assert isinstance(result, pd.DataFrame)
    assert "iso_code" in result.columns
    assert "year" in result.columns
    assert "exchange_rate" in result.columns


def test_get_exchange_rates_with_country_filter(sample_source_frames):
    """Test that get_exchange_rates filters by countries correctly."""
    result = get_imf_exchange_rates(countries=["USA", "FRA"])

    assert set(result["iso_code"].unique()) == {"USA", "FRA"}


def test_get_exchange_rates_with_year_filter(sample_source_frames):
    """Test that get_exchange_rates filters by years correctly."""
    result = get_imf_exchange_rates(years=[2021, 2022, 2023])

    assert set(result["year"].unique()) == {2021, 2022, 2023}


def test_get_exchange_rates_with_year_range_filter(sample_source_frames):
    """Test that get_exchange_rates accepts a range for years."""
    result = get_imf_exchange_rates(years=range(2021, 2024))

    assert set(result["year"].unique()) == {2021, 2022, 2023}


def test_get_exchange_rates_with_combined_filters(sample_source_frames):
    """Test that get_exchange_rates applies multiple filters correctly."""
    result = get_imf_exchange_rates(countries=["USA", "GBR"], years=range(2021, 2023))

    assert set(result["iso_code"].unique()).issubset({"USA", "GBR"})
    assert set(result["year"].unique()).issubset({2021, 2022})


def test_get_exchange_rates_use_source_codes(sample_source_frames):
    """Test that use_source_codes changes the entity column name."""
    result = get_imf_exchange_rates(use_source_codes=True)

    assert "entity_code" in result.columns
    assert "iso_code" not in result.columns


def test_get_exchange_rates_different_currencies(sample_source_frames):
    """Test that get_exchange_rates works with different currency combinations."""
    result = get_imf_exchange_rates(source_currency="USA", target_currency="EUR")

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_wb_exchange_rates_works(sample_source_frames):
    """Test that World Bank exchange rates work."""
    result = get_wb_exchange_rates()

    assert isinstance(result, pd.DataFrame)
    assert "exchange_rate" in result.columns


def test_get_oecd_dac_exchange_rates_works(sample_source_frames):
    """Test that OECD DAC exchange rates work."""
    result = get_oecd_dac_exchange_rates()

    assert isinstance(result, pd.DataFrame)
    assert "exchange_rate" in result.columns


def test_get_wb_ppp_rates_works(sample_source_frames):
    """Test that World Bank PPP rates work."""
    result = get_wb_ppp_rates()

    assert isinstance(result, pd.DataFrame)
    assert "exchange_rate" in result.columns


def test_get_exchange_rates_no_filters_returns_all(sample_source_frames):
    """Test that when no filters are applied, all data is returned."""
    result = get_imf_exchange_rates()

    # Should have multiple countries and years
    assert len(result["iso_code"].unique()) > 1
    assert len(result["year"].unique()) > 1


def test_get_exchange_rates_empty_filter_returns_empty(sample_source_frames):
    """Test that empty filter lists return empty DataFrames."""
    result = get_imf_exchange_rates(countries=[])

    assert len(result) == 0


def test_get_exchange_rates_nonexistent_country_returns_empty(sample_source_frames):
    """Test that filtering for non-existent countries returns empty DataFrame."""
    result = get_imf_exchange_rates(countries=["XXX"])

    assert len(result) == 0


def test_get_exchange_rates_same_source_target_currency(sample_source_frames):
    """Test that same source and target currency returns rate of 1."""
    result = get_imf_exchange_rates(source_currency="USA", target_currency="USA")

    assert isinstance(result, pd.DataFrame)
    # All exchange rates should be 1 when source equals target
    assert all(result["exchange_rate"] == 1.0)
