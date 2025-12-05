import pandas as pd
import pytest

from pydeflate import (
    get_imf_cpi_deflators,
    get_imf_cpi_e_deflators,
    get_imf_gdp_deflators,
    get_oecd_dac_deflators,
    get_wb_cpi_deflators,
    get_wb_gdp_deflators,
    get_wb_gdp_linked_deflators,
)
from pydeflate import imf_gdp_deflate


def test_get_imf_gdp_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting IMF GDP deflators."""
    result = get_imf_gdp_deflators(
        base_year=2022,
        source_currency="USA",
        target_currency="EUR",
        countries=["USA", "FRA", "GBR"],
        years=range(2021, 2024),
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert set(result.columns) == {"iso_code", "year", "deflator"}
    assert all(result["year"] >= 2021) and all(result["year"] < 2024)
    assert set(result["iso_code"].unique()).issubset({"USA", "FRA", "GBR"})


def test_get_imf_cpi_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting IMF CPI deflators."""
    result = get_imf_cpi_deflators(base_year=2022, countries=["USA", "GBR"])

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "deflator" in result.columns


def test_get_imf_cpi_e_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting IMF CPI-E deflators."""
    result = get_imf_cpi_e_deflators(base_year=2022, countries=["USA"])

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_wb_gdp_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting World Bank GDP deflators."""
    result = get_wb_gdp_deflators(base_year=2022, countries=["USA", "FRA"])

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_wb_gdp_linked_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting World Bank GDP linked deflators."""
    result = get_wb_gdp_linked_deflators(base_year=2022)

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_wb_cpi_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting World Bank CPI deflators."""
    result = get_wb_cpi_deflators(base_year=2022)

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_oecd_dac_deflators_full_workflow(sample_source_frames):
    """Test complete workflow of getting OECD DAC deflators."""
    result = get_oecd_dac_deflators(base_year=2022)

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_deflators_with_components(sample_source_frames):
    """Test that include_components returns additional columns."""
    result = get_imf_gdp_deflators(
        base_year=2022, countries=["USA"], include_components=True
    )

    assert isinstance(result, pd.DataFrame)
    assert "price_deflator" in result.columns
    assert "exchange_deflator" in result.columns
    assert "exchange_rate" in result.columns
    assert len(result.columns) == 6


def test_get_deflators_consistency_with_deflate(sample_source_frames):
    """Test that get_deflators returns consistent data with deflate functions."""
    # Get deflators
    deflators = get_imf_gdp_deflators(
        base_year=2022,
        source_currency="USA",
        target_currency="USA",
        countries=["USA"],
        years=[2021],
    )

    # Create test data
    test_data = pd.DataFrame({"iso_code": ["USA"], "year": [2021], "value": [100.0]})

    # Deflate using the regular function
    deflated = imf_gdp_deflate(data=test_data, base_year=2022, value_column="value")

    # Get the deflator value
    deflator_value = deflators[
        (deflators["iso_code"] == "USA") & (deflators["year"] == 2021)
    ]["deflator"].iloc[0]

    # The deflated value should equal original / deflator
    expected = 100.0 / deflator_value
    actual = deflated["value"].iloc[0]

    assert actual == pytest.approx(expected, rel=1e-6)


def test_get_deflators_to_current_vs_constant(sample_source_frames):
    """Test that to_current produces different deflators."""
    constant = get_imf_gdp_deflators(
        base_year=2022, countries=["USA"], years=[2021], to_current=False
    )

    current = get_imf_gdp_deflators(
        base_year=2022, countries=["USA"], years=[2021], to_current=True
    )

    # Both should have data
    assert len(constant) > 0
    assert len(current) > 0

    # Deflators should be different
    constant_deflator = constant["deflator"].iloc[0]
    current_deflator = current["deflator"].iloc[0]
    assert constant_deflator != current_deflator


def test_get_deflators_source_codes(sample_source_frames):
    """Test that use_source_codes works correctly."""
    result = get_imf_gdp_deflators(base_year=2022, use_source_codes=True)

    assert "entity_code" in result.columns
    assert "iso_code" not in result.columns
    assert len(result) > 0
