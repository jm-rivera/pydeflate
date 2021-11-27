#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pandas as pd

from pydeflate.get_data import oecd_data, wb_data
from pydeflate.utils import check_year_as_number

__exchange_source = {
    "wb": wb_data.get_currency_exchange,
    "oecd_dac": oecd_data.get_exchange_rate,
}


def _check_key_errors(
    rates_source: str, columns: list, value_column: str, date_column: str
) -> None:

    """Check whether provided parameters are valid"""

    if rates_source not in __exchange_source.keys():
        raise KeyError(
            f"{rates_source} is not a valid exchange rates source. "
            f"Please choose from {__exchange_source.keys()}"
        )

    if value_column not in columns:
        raise KeyError(
            f"{value_column} is not a valid column in the provided DataFrame"
        )

    if date_column not in columns:
        raise KeyError(f"{date_column} is not a valid column in the provided DataFrame")


def exchange(
    df: pd.DataFrame,
    source_currency: str,
    target_currency: str,
    rates_source: str = "wb",
    value_column: str = "value",
    target_column: str = "value_xe",
    date_column: str = "date",
) -> pd.DataFrame:
    """


    Parameters
    ----------
    df : pd.DataFrame
        A Pandas DataFrame, in long format, containing at least a date column,
        an column with iso-3 codes to identify the source currency, and a
        value column where the values to be converted are stored.
    source_currency : str
        The ISO-3 code of the country which owns the currency in which the data
        is expressed. "LCU" can be used to indicate that data is in Local
        Currency Unit. "emu" can be used for the EURO.
    target_currency : str
        The ISO-3 code of the country which owns the currency to which the data
        will be converted. "LCU" can be used to convert from a given currency
        (like the USD), back to each country's Local Currency.
    rates_source : str, optional
        The source of the exchange rate data. Current options include "wb" for
        the World Bank and "oecd_dac" for the exchange rates used for ODA
        statistics. The default is "wb".
    value_column : str, optional
        The name of the column containing the values to be converted.
        The default is "value".
    target_column : str, optional
        The name of the column where the converted values will be stored.
        The default is "value_xe".
    date_column : str, optional
        The name of the column where the date/year is stored.
        The default is "date".

    Returns
    -------
    df : pd.DataFrame
        Returns a dataframe containing the converted data stored in the
        target column.

    """

    # Check whether provided parameters are valid
    _check_key_errors(rates_source, df.columns, value_column, date_column)

    # If source currency matches target currency, do nothing
    if source_currency == target_currency:
        df[target_column] = df[value_column]
        return df

    # check whether date is provided as integer
    df, year_as_number = check_year_as_number(df, date_column)

    # check whether target currency is LCU
    if target_currency == "LCU":
        target_currency = source_currency
        source_currency = "LCU"
        target_changed = True
    else:
        target_changed = False

    # get the selected rates function
    xe = __exchange_source[rates_source](target_currency)
    xe = xe.rename(columns={"year": date_column})

    # Check source and target currencies
    if (source_currency not in set(xe.iso_code)) and (source_currency != "LCU"):
        raise KeyError(f"{source_currency} not a valid currency code")

    if (target_currency not in set(xe.iso_code)) and (target_currency != "LCU"):
        raise KeyError(f"{target_currency} not a valid target currency")

    if source_currency == "LCU":
        df = df.merge(
            xe,
            on=["iso_code", date_column],
            suffixes=("", "_xe"),
        )

    else:
        xe = xe.loc[xe.iso_code == source_currency]
        df = df.merge(
            xe.drop("iso_code", axis=1),
            on=[date_column],
            suffixes=("", "_xe"),
        )

    # revert change to target_currency if target_changed
    if target_changed:
        source_currency = target_currency
        target_currency = "LCU"

    if target_currency == "LCU":
        df[target_column] = df[value_column] * df[f"{value_column}_xe"]

    else:
        df[target_column] = df[value_column] / df[f"{value_column}_xe"]

    if year_as_number:
        df[date_column] = df[date_column].dt.year

    return df.drop(["value_xe"], axis=1)
