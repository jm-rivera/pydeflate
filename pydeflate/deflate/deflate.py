#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Callable

import pandas as pd

from pydeflate.get_data.data import Data
from pydeflate.utils import check_year_as_number

from pydeflate.deflate.deflator import Deflator
from pydeflate.get_data.imf_data import IMF
from pydeflate.get_data.oecd_data import OECD, OECD_XE
from pydeflate.get_data.wb_data import WB, WB_XE


DEFLATORS = {
    "oecd_dac": OECD,
    "wb": WB,
    "imf": IMF,
}

EXCHANGE = {"oecd_dac": OECD_XE, "wb": WB_XE, "imf": WB_XE}


def deflate(
    df: pd.DataFrame,
    base_year: int,
    source: str,
    method: Optional[str] = None,
    source_currency: str = "USA",
    target_currency: str = "USA",
    iso_column: str = "iso_code",
    date_column: str = "date",
    source_col: str = "value",
    target_col: str = "value",
    reverse: bool = False,
) -> pd.DataFrame:
    """
    Takes a DataFrame containing flows data and returns a DataFrame containing
    the deflated amounts. It can convert from current to constant (default) or
    from constant to current by specifying 'reverse' as True.

    Parameters
    ----------
    df : pd.DataFrame
        A pandas DataFrame containing data formated vertically (one row, one
        value to be deflated). The source country must be specified through a
        column with ISO-3 codes. Users can specify the name of the source
        country column, the value column and the column where the deflated
        amounts.
    base_year : int
        If converting from current to constant, the target base year for the
        constantfigures. If converting from constant, the base year of the data.
    source : {‘oecd_dac’, 'wb', 'imf'}
        The source of the data used to build the deflators. The value (and
        completness) of the price deflators may change based on the source.
        Additionally, the OECD DAC data is only available for DAC donors. Both
        the IMF and WB sources use exchange rates downloaded from the World Bank.
    method : {'gdp','gdp_linked','cpi','pcpi','pcpie', None}, optional
        The method used to calculate the price deflator:

        For World Bank (source == 'wb'):
            •'gdp': using GDP deflators.

            •'gdp_linked': a GDP deflator series which has been linked to
            produce a consistent time series to counteract breaks in series
            over time due to changes in base years, sources or methodologies.

            •'cpi': using Consumer Price Index data

        For IMF (source == 'imf'):
            •'pcpi': Consumer Price Index data

            •'pcpie': end-period Consumer Price Index (e.g for December each year).

        For OECD DAC (source == 'oecd_dac'):
            •None

        The default is None.
    source_currency : str, optional
        The iso3 code of the source currency. Note that deflators for EU countries
        are only in Euros from the year in which the Euro was adopted. To produce
        deflators only in euros, use 'emu'. The default is 'USA'.
    target_currency : str, optional
        The iso3 code of the deflated amounts. It can be the same as the source
        currency. In cases where they are different, the exchange rate will be
        applied. To produce deflators only in euros, use 'emu'. The default is 'USA'.
    iso_column : str, optional
        The column containing the iso3 codes of the data's currency.
        The default is 'USA'.
    date_column : str, optional
        The column containing the date values. The column can contain years (int)
        or datetime objects. The default is 'date'.
    source_col : str, optional
        The column containing the data to be deflated. The default is 'value'.
    target_col : str, optional
        Column where the deflated data will be stored. It can be the same as the
        source column if a copy of the original isn't needed.The default is 'value'.
    reverse : bool, optional
        If True, amounts will be treated as in constant prices and convered to
        current prices. The default is False.


    Returns
    -------
    deflator : pandas.DataFrame
        A pandas DataFrame containing the deflated data. Years for which there
        are no deflators will be returned as null values.

    """

    # keep track of original columns
    if target_col not in df.columns:
        cols = [*df.columns, target_col]
    else:
        cols = df.columns

    if source not in DEFLATORS.keys():
        raise ValueError(f'source "{source}" not valid')

    # check if date format matches
    df, year_as_number = check_year_as_number(df, date_column)

    # Define exchange and price data objects
    xe: Data = EXCHANGE[source]()
    price: Data = DEFLATORS[source](method=method)

    # Get deflator functions
    price_dfl: Callable = price.get_deflator
    x_dfl: Callable = xe.get_deflator

    # Get currency exchange data frame
    x_rate: pd.DataFrame = xe.get_data(currency_iso=target_currency)

    deflator = Deflator(
        base_year=base_year,
        xe_deflator=x_dfl,
        price_deflator=price_dfl,
        xe=x_rate,
        source_currency=source_currency,
        target_currency=target_currency,
    ).deflator()

    df = df.merge(
        deflator,
        left_on=[iso_column, date_column],
        right_on=["iso_code", "year"],
        how="left",
    )

    if reverse:
        df[target_col] = df[source_col] * (df.deflator / 100)

    else:
        df[target_col] = df[source_col] / (df.deflator / 100)

    df = df.filter(cols, axis=1)

    if year_as_number:
        df[date_column] = df[date_column].dt.year

    return df


if __name__ == "__main__":
    pass
