#!/usr/bin/env python

"""Tests for `pydeflate` package."""

import pytest


from pydeflate import deflate
from tests.test_deflate import testing_parameters as tp


def test_deflate():
    """Unit test for main deflate function"""

    df = deflate(
        df=tp.test_df_lcu,
        base_year=2020,
        source="oecd_dac",
        source_currency="LCU",
        target_currency="USA",
        iso_column="iso_code",
        date_column="date",
        source_col="value",
        target_col="value_deflated",
    )

    results = df.set_index("iso_code")["value_deflated"].to_dict()

    assert round(results["FRA"] / 1000, 1) == 10.4
    assert round(results["GBR"] / 1000, 1) == 19.3
    assert round(results["USA"] / 1000, 1) == 34.8
    assert round(results["CAN"] / 1000, 1) == 4.5


def test_deflate_reversed():
    """Unit test for main deflate function, with reversed option"""
    df = deflate(
        df=tp.test_df_usd,
        base_year=2020,
        source="oecd_dac",
        method="test_print",
        source_currency="USA",
        target_currency="FRA",
        iso_column="iso_code",
        date_column="date",
        source_col="value",
        target_col="value_deflated",
    )

    results = df.set_index("iso_code")["value"].to_dict()

    rev = deflate(
        df=df,
        base_year=2020,
        source="oecd_dac",
        source_currency="USA",
        target_currency="FRA",
        iso_column="iso_code",
        date_column="date",
        source_col="value_deflated",
        target_col="value_deflated",
        reverse=True,
    )

    rev_results = rev.set_index("iso_code")["value_deflated"].to_dict()

    assert round(results["FRA"] / 100, 1) == round(rev_results["FRA"] / 100, 1)
    assert round(results["GBR"] / 100, 1) == round(rev_results["GBR"] / 100, 1)
    assert round(results["USA"] / 100, 1) == round(rev_results["USA"] / 100, 1)
    assert round(results["CAN"] / 100, 1) == round(rev_results["CAN"] / 100, 1)


@pytest.mark.parametrize(*tp.deflate_errors)
def test_deflate_errors(
    df,
    base_year,
    source,
    method,
    source_currency,
    target_currency,
    iso_column,
    date_column,
    source_col,
    target_col,
):

    with pytest.raises(Exception):
        deflate(
            df,
            base_year,
            source,
            method,
            source_currency,
            target_currency,
            iso_column,
            date_column,
            source_col,
            target_col,
        )
