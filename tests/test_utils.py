#!/usr/bin/env python

"""Tests for `pydeflate` package."""

import pytest


from pydeflate import utils


def test_update_gdp():
    # download the data using WB API
    constant, current = utils.update_gdp(test=True)

    if (constant is None) or (current is None):
        raise AssertionError('Could not use WBGAPI to download data')

    # check if the base year continues to be 2010, and if data downloaded correctly
    constant = constant.loc[(constant.year == 2010) &
                            (constant.iso_code == 'USA')]
    current = current.loc[(current.year == 2010) & (current.iso_code == 'USA')]

    result = int(current.value/constant.value)

    assert result == 1


def test_update_exchange():
    exchange = utils.update_exchange(test=True)

    if exchange is None:
        raise AssertionError('Could not use WBGAPI to download data')

    assert int(exchange.loc[(exchange.year == 2010) &
                            (exchange.iso_code == 'USA')].value) == 1


def test_update_data():
    ...


def test_clean_df():
    ...


def test_exchange_rates():
    ...


def test_country_rebase():
    ...


def test_gdp_deflator():
    ...


def test_exchange_deflator():
    ...


def test_gdp_xe_deflator():
    ...


def test_gdp_factor():
    ...
