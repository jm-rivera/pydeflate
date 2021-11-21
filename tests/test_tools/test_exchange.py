#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 13:44:34 2021

@author: jorge
"""

from pydeflate.tools import exchange
import pandas as pd
import pytest

empty_df = pd.DataFrame([{}])

test_df = pd.DataFrame(
    {
        "iso_code": ["FRA", "GBR", "USA"],
        "date": [2010, 2015, 2018],
        "value": [100, 100, 100],
    }
)

errors = (
    (
        "df, source_currency, target_currency, rates_source, value_column,"
        "target_column, date_column"
    ),
    [
        (empty_df, "USA", "FRA", "wb", "value", "value_xe", "date"),
        (test_df, "random_source", "FRA", "wb", "value", "value_xe", "date"),
        (test_df, "USA", "random_target", "wb", "value", "value_xe", "date"),
        (test_df, "USA", "FRA", "random_source", "value", "value_xe", "date"),
        (test_df, "USA", "FRA", "wb", "random_col", "value_xe", "date"),
        (test_df, "USA", "FRA", "wb", "value", "value_xe", "random_col"),
    ],
)


def test_exchange_to_LCU():

    result = exchange.exchange(
        df=test_df.copy(),
        source_currency="GTM",
        target_currency="LCU",
        rates_source="wb",
        value_column="value",
        target_column="xe",
        date_column="date",
    )

    result = result.set_index("iso_code")["xe"].to_dict()
    assert round(result["FRA"], 0) == 9
    assert round(result["GBR"], 0) == 9
    assert round(result["USA"], 0) == 13


def test_exchange_to_nonUS():

    result = exchange.exchange(
        df=test_df.copy(),
        source_currency="LCU",
        target_currency="GTM",
        rates_source="wb",
        value_column="value",
        target_column="value",
        date_column="date",
    )

    result = result.set_index("iso_code")["value"].to_dict()
    assert round(result["FRA"], 0) == 1068
    assert round(result["GBR"], 0) == 1169
    assert round(result["USA"], 0) == 752


def test_exchange_nonUS_to_nonUS():

    result = exchange.exchange(
        df=test_df.copy(),
        source_currency="FRA",
        target_currency="GTM",
        rates_source="wb",
        value_column="value",
        target_column="xe",
        date_column="date",
    )

    result = result.set_index("iso_code")["xe"].to_dict()
    assert round(result["FRA"], 0) == 1068
    assert round(result["GBR"], 0) == 849
    assert round(result["USA"], 0) == 888


def test_exchange_target_to_source():

    result = exchange.exchange(
        df=test_df.copy(),
        source_currency="FRA",
        target_currency="FRA",
        rates_source="wb",
        value_column="value",
        target_column="xe",
        date_column="date",
    )

    result = result.set_index("iso_code")["xe"].to_dict()
    assert round(result["FRA"], 0) == 100
    assert round(result["GBR"], 0) == 100
    assert round(result["USA"], 0) == 100


@pytest.mark.parametrize(*errors)
def test_exchange_errors(
    df,
    source_currency,
    target_currency,
    rates_source,
    value_column,
    target_column,
    date_column,
) -> None:

    with pytest.raises(Exception):
        exchange.exchange(
            df=df,
            source_currency=source_currency,
            target_currency=target_currency,
            rates_source=rates_source,
            value_column=value_column,
            target_column=target_column,
            date_column=date_column,
        )
