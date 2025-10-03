from unittest.mock import Mock

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


def test_convert_id_uses_additional_mapping(monkeypatch):
    series = pd.Series(["European Union", "Custom"], name="region")

    mocked = Mock()
    mocked.get_iso3_country_code_fuzzy.return_value = ["EUR", None]
    monkeypatch.setattr("pydeflate.sources.common.Country", lambda: mocked)

    converted = convert_id(
        series,
        from_type="regex",
        to_type="ISO3",
        additional_mapping={"Custom": "CUS"},
    )

    assert list(converted) == ["EUR", "CUS"]


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
    assert rebased.loc[rebased["year"] == 2022, "EXCHANGE_D"].iloc[0] == pytest.approx(100.0)
    assert rebased.loc[rebased["year"] == 2021, "EXCHANGE_D"].iloc[0] == pytest.approx(110.0)
