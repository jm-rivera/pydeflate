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
    to_current: bool = False,
    iso_column: Union[str, None] = None,
) -> pd.DataFrame:
    """Deflate amounts to a given currency - base year combination.

    Takes a DataFrame containing flows data and returns a DataFrame containing
    the deflated amounts. It can also convert from constant to current by specifying
    to_current as 'True'.

    Args:
        df: the DataFrame containing the flows column to be deflated. If multiple
            columns need to be deflated, the function needs to be called multiple times.
        base_year: If converting from current to constant, the target base year for the
            constant figures. If converting from constant, the base year of the data.
        source:{‘oecd_dac’, 'wb', 'imf'}
            The source of the data used to build the deflators. The value (and
            completeness) of the price deflators may change based on the source.
            Additionally, the OECD DAC data is only available for DAC donors. Both
            the IMF and WB sources use exchange rates downloaded from the World Bank.
        method:{'gdp', 'gdp_linked', 'cpi', 'pcpi', 'pcpie', None}
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

        source_currency: The iso3 code of the source currency. Note that deflators for EU countries
            are only in Euros from the year in which the Euro was adopted. To produce
            deflators only in euros, use 'emu'.

        target_currency :The iso3 code of the deflated amounts. It can be the same as the source
            currency. In cases where they are different, the exchange rate will be
            applied. To produce deflators only in euros, use 'emu'.

        id_column: The column containing the id codes (iso3 codes, for example) of the data's currency.

        id_type:The classification type for the id_column. By default, ISO3 but others are possible.
            Any options used in the Country Converter package are valid. For the OECD DAC classification, use 'DAC'.

        date_column:The column containing the date values. The column can contain years (int)
            or datetime objects.

        source_col:The column containing the data to be deflated.

        target_col: Column where the deflated data will be stored. It can be the same as the
            source column if a copy of the original isn't needed.

        to_current: If True, amounts will be treated as in constant prices and converted to current prices.

        iso_column:Provided for backwards compatibility. It is essentially an alias for id_column

    Returns:
        A pandas DataFrame containing the deflated data. Years for which there
        are no deflators will be returned as null values.


    """
    # copy the dataframe to avoid modifying the original
    df = df.copy(deep=True)

    # Backwards compatibility: if the iso_column parameter is used, reassign it to
    # the ID column
    if iso_column is not None:
        id_column = iso_column

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
    x_rate: pd.DataFrame = xe.get_data(
        currency_iso=target_currency if not to_current else source_currency
    ).copy(deep=True)

    # Create a Deflator object and get the deflator DataFrame.
    deflator = (
        Deflator(
            base_year=base_year,
            xe_deflator=x_dfl,
            price_deflator=price_dfl,
            xe=x_rate,
            source_currency=source_currency if not to_current else target_currency,
            target_currency=target_currency if not to_current else source_currency,
        )
        .deflator()
        .rename(columns={"iso_code": "id_", "year": date_column})
    )

    # Merge the original data with the deflator DataFrame
    df = df.merge(
        deflator,
        on=["id_", date_column],
        how="left",
        suffixes=("", "_"),
    )

    # If the reverse option is used, multiply the data. Else divide.
    if to_current:
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
