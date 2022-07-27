from typing import Union

import pandas as pd

from pydeflate.get_data.oecd_data import OECD_XE
from pydeflate.get_data.wb_data import WB_XE
from pydeflate.utils import check_year_as_number, to_iso3, oecd_codes

__exchange_source = {
    "wb": WB_XE().get_data,
    "oecd_dac": OECD_XE().get_data,
}


def _check_key_errors(
    rates_source: str,
    columns: Union[list, pd.Index],
    value_column: str,
    date_column: str,
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
    id_column: str = "iso_code",
    id_type: str = "ISO3",
    value_column: str = "value",
    target_column: str = "value_xe",
    date_column: str = "date",
) -> pd.DataFrame:
    """


    Parameters
    ----------
    df : pd.DataFrame
        A Pandas DataFrame, in long format, containing at least a date column,
        a column with iso-3 codes to identify the source currency, and a
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
    id_column : str, optional
        The name of the column containing the codes or names used to identify countries.
        The default is "iso_code".
    id_type : str, optional
        The types of codes used to identify countries. Should match options in
        Country Converter or the DAC codes.The default is "ISO3".
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

    # create a copy of the dataframe to avoid modifying the original
    df = df.copy(deep=True)

    # Check whether provided parameters are valid
    _check_key_errors(rates_source, df.columns, value_column, date_column)

    # If source currency matches target currency, do nothing
    if source_currency == target_currency:
        df[target_column] = df[value_column]
        return df

    # keep track of original columns. This is so that the same order and columns can be
    # preserved.
    if target_column not in df.columns:
        cols = [*df.columns, target_column]
    else:
        cols = df.columns

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

    # rename the column names in Xe to match the provided DataFrame
    xe = xe.rename(
        columns={"year": date_column, "value": value_column, "iso_code": "id_"}
    )

    # Create ID col.  By default, if a country does not have a DAC deflator, the
    # DAC,Total deflator is used.
    if id_type == "DAC":
        df["id_"] = df[id_column].map(oecd_codes).fillna("DAC")
    else:
        df = df.pipe(
            to_iso3, codes_col=id_column, target_col="id_", src_classification=id_type
        )

    # Check source and target currencies
    if (source_currency not in set(xe.id_)) and (source_currency != "LCU"):
        raise KeyError(f"{source_currency} not a valid currency code")

    if (target_currency not in set(xe.id_)) and (target_currency != "LCU"):
        raise KeyError(f"{target_currency} not a valid target currency")

    if source_currency == "LCU":
        df = df.merge(
            xe,
            on=["id_", date_column],
            suffixes=("", "_xe"),
        )

    else:
        xe = xe.loc[xe.id_ == source_currency]
        df = df.merge(
            xe.drop("id_", axis=1),
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

    return df.filter(cols, axis=1)
