#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import Callable

import numpy as np
import pandas as pd

from pydeflate import utils
from pydeflate.get_data import imf_data, oecd_data, wb_data


def _get_and_deflate(
    function: Callable,
    base_year: int,
    target_currency: str = None,
    col: str = "value",
) -> pd.DataFrame:
    """Get data using a specific function and apply an exchange rate
    and deflators if provided"""

    if target_currency is None:
        df = function()
    else:
        df = function(currency_iso=target_currency)

    if base_year not in df.year.dt.year.unique():
        raise ValueError(f"Base year ({base_year}) not valid.")

    df[col] = utils.rebase(df, base_year)

    return df


def __align_currencies(
    deflator: pd.DataFrame,
    source_currency: str,
    target_currency: str,
    source: str,
) -> pd.DataFrame:

    """Check whether an exchange rate needs to be applied to a deflator set
    in order to properly convert data from source to target currency"""

    # If both the source and target currency match, do nothing
    if source_currency == target_currency:
        return deflator

    if source == "wb":
        xe = wb_data.get_currency_exchange(target_currency)
    elif source == "oecd_dac":
        xe = oecd_data.get_exchange_rate(target_currency)

    if source_currency == "LCU":
        deflator = deflator.merge(xe, on=["iso_code", "year"], suffixes=("", "_xe"))
        deflator.value = deflator.value * deflator.value_xe

    else:
        xe = xe.loc[xe.iso_code == source_currency]
        deflator = deflator.merge(
            xe.drop("iso_code", axis=1), on=["year"], suffixes=("", "_xe")
        )
        deflator.value = deflator.value * deflator.value_xe

    # Check if data is valid
    if int(deflator.value_xe.sum()) == 0:
        raise ValueError(f"Data for {source_currency} is not valid")

    return deflator.drop("value_xe", axis=1)


def _align_currencies_wb(
    deflator: pd.DataFrame,
    source_currency: str,
    target_currency: str,
) -> pd.DataFrame:

    """Check whether an exchange rate needs to be applied to a deflator set
    in order to properly convert data from source to target currency"""

    return __align_currencies(
        deflator=deflator,
        source_currency=source_currency,
        target_currency=target_currency,
        source="wb",
    )


def _align_currencies_dac(
    deflator: pd.DataFrame,
    source_currency: str,
    target_currency: str,
) -> pd.DataFrame:

    """Check whether an exchange rate needs to be applied to a deflator set
    in order to properly convert data from source to target currency"""

    return __align_currencies(
        deflator=deflator,
        source_currency=source_currency,
        target_currency=target_currency,
        source="oecd_dac",
    )


def _defl_pipeline(
    exchange_deflator: Callable,
    price_deflator: Callable,
    currency_align: Callable,
    base_year: int,
    source_currency: str,
    target_currency: str,
) -> pd.DataFrame:

    """Returns a dataframe with price-currency deflators.
    -exchange_deflator takes in a Callable to get exchange rate deflators.
    -price_deflator takes in a Callable to get gdp/price deflators.
    -base_year takes an integer as the base year for the deflators.
    """

    # get exchange rate and rebase
    xed = _get_and_deflate(exchange_deflator, base_year, target_currency)

    # get price deflators and rebase
    prd = _get_and_deflate(price_deflator, base_year)

    df = prd.merge(xed, on=["iso_code", "year"], how="left", suffixes=("_def", "_xe"))

    df["value"] = round(100 * df.value_def / df.value_xe, 2)

    return (
        df.filter(["iso_code", "year", "value"], axis=1)
        .replace(0, np.nan)
        .dropna(subset=["value"])
        .reset_index(drop=True)
        .pipe(currency_align, source_currency, target_currency)
        .rename(columns={"value": "deflator"})
    )


def oecd_dac_deflators(
    base_year: int,
    source_currency: str = "LCU",
    target_currency: str = "USA",
    **kwargs,
) -> pd.DataFrame:
    """Get OECD deflators for a given base_year"""

    return _defl_pipeline(
        exchange_deflator=oecd_data.get_xe_deflator,
        price_deflator=oecd_data.get_gdp_deflator,
        currency_align=_align_currencies_dac,
        base_year=base_year,
        source_currency=source_currency,
        target_currency=target_currency,
    )


def wb_deflators(
    base_year: int,
    method: str,
    source_currency: str = "LCU",
    target_currency: str = "USA",
) -> pd.DataFrame:
    """Get WB deflators for a given base_year.
    - method can be:
        'gdp': to use GDP deflators,
        'gdp_linked': to use the WB linked series of GDP deflators
        'cpi': to use price inflation deflators
    """

    methods = wb_data.available_methods()

    # Error handling for provided method
    utils.check_method(method, methods)

    return _defl_pipeline(
        exchange_deflator=wb_data.get_xe_deflator,
        price_deflator=methods[method],
        currency_align=_align_currencies_wb,
        base_year=base_year,
        source_currency=source_currency,
        target_currency=target_currency,
    )


def imf_deflators(
    base_year: int,
    method: str,
    source_currency: str = "LCU",
    target_currency: str = "USA",
) -> pd.DataFrame:

    """Get IMF deflators for a given base year.
    - method can be:
        'gdp' : to use GDP deflators
        'pcpi': to use
        'pcpie' to use
    """

    methods = imf_data.available_methods()

    # Error handling for provided method
    utils.check_method(method, methods)

    return _defl_pipeline(
        exchange_deflator=wb_data.get_xe_deflator,
        currency_align=_align_currencies_wb,
        price_deflator=methods[method],
        base_year=base_year,
        source_currency=source_currency,
        target_currency=target_currency,
    )


if __name__ == "__main__":

    pass
