#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Callable, Union

import pandas as pd

from pydeflate.deflate.deflator import Deflator
from pydeflate.get_data.data import Data
from pydeflate.get_data.imf_data import IMF
from pydeflate.get_data.oecd_data import OECD, OECD_XE
from pydeflate.get_data.wb_data import WB, WB_XE
from pydeflate.utils import check_year_as_number, to_iso3, oecd_codes

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
    id_column: str = "iso_code",
    id_type: str = "ISO3",
    date_column: str = "date",
    source_col: str = "value",
    target_col: str = "value",
    reverse: bool = False,
    iso_column: Union[str, None] = None,
) -> pd.DataFrame:
    """
    Takes a DataFrame containing flows data and returns a DataFrame containing
    the deflated amounts. It can convert from current to constant (default) or
    from constant to current by specifying 'reverse' as True.

    Parameters
    ----------
    df : pd.DataFrame
        A pandas DataFrame containing data formatted vertically (one row, one
        value to be deflated). The source country must be specified through a
        column with ISO-3 codes. Users can specify the name of the source
        country column, the value column and the column where the deflated
        amounts.
    base_year : int
        If converting from current to constant, the target base year for the
        constant figures. If converting from constant, the base year of the data.
    source : {‘oecd_dac’, 'wb', 'imf'}
        The source of the data used to build the deflators. The value (and
        completeness) of the price deflators may change based on the source.
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

            •'pcpie': end-period Consumer Price Index (e.g. for December each year).

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
    id_column : str, optional
        The column containing the id codes (iso3 codes, for example) of the data's currency.
        The default is 'iso_code'.
    id_type : str, optional
        The classification type for the id_column. By default, ISO3 but others are possible.
         For the OECD DAC classification, use 'DAC'
    date_column : str, optional
        The column containing the date values. The column can contain years (int)
        or datetime objects. The default is 'date'.
    source_col : str, optional
        The column containing the data to be deflated. The default is 'value'.
    target_col : str, optional
        Column where the deflated data will be stored. It can be the same as the
        source column if a copy of the original isn't needed.The default is 'value'.
    reverse : bool, optional
        If True, amounts will be treated as in constant prices and converted to
        current prices. The default is False.
    iso_column : str, optional
        Provided for backwards compatibility. It is essentially an alias for id_column


    Returns
    -------
    deflator : pandas.DataFrame
        A pandas DataFrame containing the deflated data. Years for which there
        are no deflators will be returned as null values.

    """
    # Backwards compatibility: if the iso_column parameter is used, reassign it to
    # the ID column
    if iso_column is not None:
        id_column = iso_column

    # Check if the reverse option (i.e. from constant to current is used). If so,
    # then also switch the target and source currencies.
    if reverse:
        sc = source_currency
        source_currency = target_currency
        target_currency = sc

    # keep track of original columns. This is so that the same order and columns can be
    # preserved.
    if target_col not in df.columns:
        cols = [*df.columns, target_col]
    else:
        cols = df.columns

    # Check if the source specified is part of the available deflators source
    if source not in DEFLATORS.keys():
        raise ValueError(f'source "{source}" not valid')

    # check if date format matches
    df, year_as_number = check_year_as_number(df, date_column)

    # Create ID col.  By default, if a country does not have a DAC deflator, the
    # DAC,Total deflator is used.
    if id_type == "DAC":
        df["id_"] = df[id_column].map(oecd_codes).fillna("DAC")
    else:
        df = df.pipe(
            to_iso3, codes_col=id_column, target_col="id_", src_classification=id_type
        )

    # Create exchange and price data objects. The specific objects created depend on the
    # source and/or method specified
    xe: Data = EXCHANGE[source]()
    price: Data = DEFLATORS[source](method=method)

    # Get deflator functions. The Deflator object takes in functions (as Callables)
    # instead of taking in the actual data.
    price_dfl: Callable = price.get_deflator
    x_dfl: Callable = xe.get_deflator

    # Get currency exchange DataFrame. This is based on the target currency
    x_rate: pd.DataFrame = xe.get_data(currency_iso=target_currency).copy()

    # Create a Deflator object and get the deflator DataFrame.
    deflator = Deflator(
        base_year=base_year,
        xe_deflator=x_dfl,
        price_deflator=price_dfl,
        xe=x_rate,
        source_currency=source_currency,
        target_currency=target_currency,
    ).deflator()

    # Merge the original data with the deflator DataFrame
    df = df.merge(
        deflator,
        left_on=["id_", date_column],
        right_on=["iso_code", "year"],
        how="left",
        suffixes=("", "_"),
    )

    # If the reverse option is used, multiply the data. Else divide.
    if reverse:
        df[target_col] = df[source_col] * (df.deflator / 100)

    else:
        df[target_col] = df[source_col] / (df.deflator / 100)

    # Keep only the columns present in the original DataFrame (including order)
    df = df.filter(cols, axis=1)

    # If the year is passed as a number, convert it back to a number.
    if year_as_number:
        df[date_column] = df[date_column].dt.year

    return df


if __name__ == "__main__":
    pass
