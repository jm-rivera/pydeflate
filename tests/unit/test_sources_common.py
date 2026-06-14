import pandas as pd
import pytest

from pydeflate.sources.common import (
    compute_exchange_deflator,
    convert_id,
    identify_base_year,
    prefix_pydeflate_to_columns,
)


def test_prefix_pydeflate_to_columns_adds_prefix_once():
    df = pd.DataFrame({"foo": [1], "pydeflate_bar": [2]})

    renamed = prefix_pydeflate_to_columns(df.copy(), prefix="pydeflate_")

    assert list(renamed.columns) == ["pydeflate_foo", "pydeflate_bar"]


def test_convert_id_resolves_aggregate_and_country():
    series = pd.Series(["European Union", "France"], name="region")

    converted = convert_id(series)

    assert list(converted) == ["EU", "FRA"]


def test_convert_id_passthrough_on_unresolved():
    """Unresolved names pass through when not_found=None."""
    series = pd.Series(["Not A Country"], name="region")

    converted = convert_id(series)

    assert list(converted) == ["Not A Country"]


def test_convert_id_not_found_value():
    """Unresolved names take not_found value when supplied."""
    series = pd.Series(["Not A Country"], name="region")

    converted = convert_id(series, not_found=pd.NA)

    assert pd.isna(converted.iloc[0])


def test_identify_base_year_returns_first_match():
    df = pd.DataFrame({"year": [2020, 2021, 2022], "NGDP_D": [95, 100, 102]})
    assert identify_base_year(df, measure="NGDP_D") == 2021


def test_compute_exchange_deflator_adds_rebased_column():
    df = pd.DataFrame(
        {
            "entity": ["USA", "USA", "USA"],
            "entity_code": ["001"] * 3,
            "year": [2021, 2022, 2023],
            "EXCHANGE": [1.1, 1.0, 0.9],
            "NGDP_D": [90.0, 100.0, 110.0],
        }
    )

    rebased = compute_exchange_deflator(
        df,
        base_year_measure="NGDP_D",
        exchange="EXCHANGE",
        year="year",
        grouper=["entity", "entity_code"],
    )

    assert "EXCHANGE_D" in rebased.columns
    assert rebased.loc[rebased["year"] == 2022, "EXCHANGE_D"].iloc[0] == pytest.approx(
        100.0
    )
    assert rebased.loc[rebased["year"] == 2021, "EXCHANGE_D"].iloc[0] == pytest.approx(
        110.0
    )
