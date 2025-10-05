import pandas as pd
import pytest

from pydeflate import (
    get_imf_exchange_rates,
    get_oecd_dac_exchange_rates,
    get_wb_exchange_rates,
    get_wb_ppp_rates,
)
from pydeflate import imf_exchange


def test_get_imf_exchange_rates_full_workflow(sample_source_frames):
    """Test complete workflow of getting IMF exchange rates."""
    result = get_imf_exchange_rates(
        source_currency="USA",
        target_currency="EUR",
        countries=["USA", "FRA", "GBR"],
        years=range(2021, 2024),
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert set(result.columns) == {"iso_code", "year", "exchange_rate"}
    assert all(result["year"] >= 2021) and all(result["year"] < 2024)
    assert set(result["iso_code"].unique()).issubset({"USA", "FRA", "GBR"})


def test_get_wb_exchange_rates_full_workflow(sample_source_frames):
    """Test complete workflow of getting World Bank exchange rates."""
    result = get_wb_exchange_rates(countries=["USA", "FRA"])

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "exchange_rate" in result.columns


def test_get_oecd_dac_exchange_rates_full_workflow(sample_source_frames):
    """Test complete workflow of getting OECD DAC exchange rates."""
    result = get_oecd_dac_exchange_rates()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "exchange_rate" in result.columns


def test_get_wb_ppp_rates_full_workflow(sample_source_frames):
    """Test complete workflow of getting World Bank PPP rates."""
    result = get_wb_ppp_rates()

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "exchange_rate" in result.columns


def test_get_exchange_rates_consistency_with_exchange(sample_source_frames):
    """Test that get_exchange_rates returns consistent data with exchange functions."""
    # Get exchange rates
    rates = get_imf_exchange_rates(
        source_currency="USA",
        target_currency="EUR",
        countries=["FRA"],
        years=[2021],
    )

    # Create test data
    test_data = pd.DataFrame({"iso_code": ["FRA"], "year": [2021], "value": [100.0]})

    # Exchange using the regular function
    exchanged = imf_exchange(
        data=test_data,
        source_currency="USA",
        target_currency="EUR",
        value_column="value",
    )

    # Get the exchange rate value
    rate_value = rates[
        (rates["iso_code"] == "FRA") & (rates["year"] == 2021)
    ]["exchange_rate"].iloc[0]

    # The exchanged value should equal original * rate
    expected = 100.0 * rate_value
    actual = exchanged["value"].iloc[0]

    assert actual == pytest.approx(expected, rel=1e-6)


def test_get_exchange_rates_lcu_to_usd(sample_source_frames):
    """Test LCU to USD exchange rates."""
    result = get_imf_exchange_rates(
        source_currency="LCU", target_currency="USA", countries=["FRA"]
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    # Exchange rates should be positive
    assert all(result["exchange_rate"] > 0)


def test_get_exchange_rates_eur_to_gbp(sample_source_frames):
    """Test EUR to GBP exchange rates."""
    result = get_imf_exchange_rates(
        source_currency="EUR", target_currency="GBP", years=[2021]
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_get_exchange_rates_source_codes(sample_source_frames):
    """Test that use_source_codes works correctly."""
    result = get_imf_exchange_rates(use_source_codes=True)

    assert "entity_code" in result.columns
    assert "iso_code" not in result.columns
    assert len(result) > 0


def test_get_wb_ppp_rates_no_target_currency():
    """Test that PPP rates don't accept target_currency parameter."""
    # The get_wb_ppp_rates function has target_currency fixed to 'PPP'
    # This test just verifies the function works without that parameter
    result = get_wb_ppp_rates(source_currency="USA")

    assert isinstance(result, pd.DataFrame)


def test_get_exchange_rates_common_currencies(sample_source_frames):
    """Test that common currency codes work (USD, EUR, GBP, etc.)."""
    result = get_imf_exchange_rates(
        source_currency="USD", target_currency="EUR", countries=["USA"]
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
