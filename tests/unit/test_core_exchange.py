import pandas as pd
import pytest

from pydeflate.core.exchange import Exchange
from pydeflate.core.source import WorldBank


def test_convert_exchange_raises_for_unknown_currency():
    source = WorldBank()
    exchange = Exchange(source=source, source_currency="USA", target_currency="USA")

    with pytest.raises(ValueError, match="No currency exchange data"):
        exchange._convert_exchange("XYZ")


def test_exchange_rate_builds_multiplier_between_currencies():
    source = WorldBank()
    exchange = Exchange(source=source, source_currency="USA", target_currency="FRA")

    fra_2022 = exchange.exchange_data.loc[
        (exchange.exchange_data["pydeflate_iso3"] == "USA")
        & (exchange.exchange_data["pydeflate_year"] == 2022)
    ]["pydeflate_EXCHANGE"].iloc[0]

    assert fra_2022 == pytest.approx(0.84, rel=1e-6)


def test_exchange_applies_multiplier_to_values():
    source = WorldBank()
    exchange = Exchange(source=source, source_currency="USA", target_currency="FRA")

    df = pd.DataFrame(
        {
            "iso_code": ["USA", "USA"],
            "year": [2021, 2022],
            "value": [100.0, 150.0],
        }
    )

    converted = exchange.exchange(
        data=df,
        entity_column="iso_code",
        year_column="year",
        value_column="value",
    )

    expected_rate_2021 = 0.83
    expected_rate_2022 = 0.84

    assert converted.loc[0, "value"] == pytest.approx(
        100.0 / expected_rate_2021, rel=1e-6
    )
    assert converted.loc[1, "value"] == pytest.approx(
        150.0 / expected_rate_2022, rel=1e-6
    )
