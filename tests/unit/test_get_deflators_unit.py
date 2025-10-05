import pandas as pd
import pytest

from pydeflate import get_imf_gdp_deflators, get_wb_cpi_deflators


def test_get_deflators_returns_dataframe(sample_source_frames):
    """Test that get_deflators returns a DataFrame with expected columns."""
    result = get_imf_gdp_deflators(base_year=2022)

    assert isinstance(result, pd.DataFrame)
    assert "iso_code" in result.columns
    assert "year" in result.columns
    assert "deflator" in result.columns


def test_get_deflators_with_country_filter(sample_source_frames):
    """Test that get_deflators filters by countries correctly."""
    result = get_imf_gdp_deflators(base_year=2022, countries=["USA", "FRA"])

    assert set(result["iso_code"].unique()) == {"USA", "FRA"}


def test_get_deflators_with_year_filter(sample_source_frames):
    """Test that get_deflators filters by years correctly."""
    result = get_imf_gdp_deflators(base_year=2022, years=[2021, 2022, 2023])

    assert set(result["year"].unique()) == {2021, 2022, 2023}


def test_get_deflators_with_year_range_filter(sample_source_frames):
    """Test that get_deflators accepts a range for years."""
    result = get_imf_gdp_deflators(base_year=2022, years=range(2021, 2024))

    assert set(result["year"].unique()) == {2021, 2022, 2023}


def test_get_deflators_with_combined_filters(sample_source_frames):
    """Test that get_deflators applies multiple filters correctly."""
    result = get_imf_gdp_deflators(
        base_year=2022, countries=["USA", "GBR"], years=range(2021, 2023)
    )

    assert set(result["iso_code"].unique()).issubset({"USA", "GBR"})
    assert set(result["year"].unique()).issubset({2021, 2022})


def test_get_deflators_include_components(sample_source_frames):
    """Test that include_components adds extra columns."""
    result_without = get_imf_gdp_deflators(base_year=2022, include_components=False)
    result_with = get_imf_gdp_deflators(base_year=2022, include_components=True)

    assert len(result_without.columns) == 3
    assert len(result_with.columns) == 6
    assert "price_deflator" in result_with.columns
    assert "exchange_deflator" in result_with.columns
    assert "exchange_rate" in result_with.columns


def test_get_deflators_use_source_codes(sample_source_frames):
    """Test that use_source_codes changes the entity column name."""
    result = get_imf_gdp_deflators(base_year=2022, use_source_codes=True)

    assert "entity_code" in result.columns
    assert "iso_code" not in result.columns


def test_get_deflators_base_year_validation():
    """Test that base_year must be an integer."""
    with pytest.raises(ValueError, match="must be an integer"):
        get_imf_gdp_deflators(base_year="2022")


def test_get_deflators_different_currencies(sample_source_frames):
    """Test that get_deflators works with different currency combinations."""
    result = get_imf_gdp_deflators(
        base_year=2022, source_currency="USA", target_currency="EUR"
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_deflators_to_current(sample_source_frames):
    """Test that to_current parameter works."""
    result_constant = get_imf_gdp_deflators(base_year=2022, to_current=False)
    result_current = get_imf_gdp_deflators(base_year=2022, to_current=True)

    # Both should return data, but with different deflator values
    assert len(result_constant) > 0
    assert len(result_current) > 0
    # The deflators should be different
    assert not result_constant["deflator"].equals(result_current["deflator"])


def test_get_wb_cpi_deflators_works(sample_source_frames):
    """Test that World Bank CPI deflators work."""
    result = get_wb_cpi_deflators(base_year=2022)

    assert isinstance(result, pd.DataFrame)
    assert "deflator" in result.columns


def test_get_deflators_no_filters_returns_all(sample_source_frames):
    """Test that when no filters are applied, all data is returned."""
    result = get_imf_gdp_deflators(base_year=2022)

    # Should have multiple countries and years
    assert len(result["iso_code"].unique()) > 1
    assert len(result["year"].unique()) > 1


def test_get_deflators_empty_filter_returns_empty(sample_source_frames):
    """Test that empty filter lists return empty DataFrames."""
    result = get_imf_gdp_deflators(base_year=2022, countries=[])

    assert len(result) == 0


def test_get_deflators_nonexistent_country_returns_empty(sample_source_frames):
    """Test that filtering for non-existent countries returns empty DataFrame."""
    result = get_imf_gdp_deflators(base_year=2022, countries=["XXX"])

    assert len(result) == 0
