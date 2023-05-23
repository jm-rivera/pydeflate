import pandas as pd

from pydeflate.deflate.deflator import Deflator
from pydeflate.get_data.exchange_data import (
    ExchangeIMF,
    ExchangeOECD,
    ExchangeWorldBank,
)
from pydeflate.get_data.imf_data import IMF
from pydeflate.get_data.oecd_data import OECD
from pydeflate.get_data.wb_data import WorldBank
from pydeflate.pydeflate_config import logger
from pydeflate.utils import check_year_as_number, oecd_codes, to_iso3

ValidDeflatorSources: dict = {
    "oecd_dac": "dac_deflator",
    "dac": "dac_deflator",
    "wb": "world_bank",
    "world_bank": "world_bank",
    "imf": "imf",
}

ValidDeflatorMethods: dict = {
    "oecd_dac": ["dac_deflator"],
    "world_bank": ["gdp", "gdp_linked", "cpi"],
    "imf": ["gdp", "pcpi", "pcpie"],
}

ValidExchangeSources: dict = {
    "oecd_dac": "oecd_dac",
    "dac": "oecd_dac",
    "wb": "world_bank",
    "world_bank": "world_bank",
    "imf": "world_bank",
}

ValidExchangeMethods: dict = {
    "oecd_dac": ["implied"],
    "world_bank": ["yearly_average", "effective_exchange"],
    "imf": ["implied"],
}

ExchangeSources: dict = {
    "oecd_dac": {
        "implied": ExchangeOECD(method="implied"),
    },
    "world_bank": {
        "yearly_average": ExchangeWorldBank(method="yearly_average"),
        "effective_exchange": ExchangeWorldBank(method="effective_exchange"),
    },
    "imf": {
        "implied": ExchangeIMF(method="implied"),
    },
}

DeflatorSources: dict = {
    "oecd_dac": OECD,
    "world_bank": WorldBank,
    "imf": IMF,
}


def _validate_deflator_source(deflator_source) -> str:
    if deflator_source not in ValidDeflatorSources:
        raise ValueError(f'"{deflator_source=}" not valid')
    return deflator_source


def _validate_deflator_method(deflator_source, deflator_method) -> str:
    # Check if the method specified is part of the available deflators methods
    if (
        deflator_method is not None
        and deflator_method not in ValidDeflatorMethods[deflator_source]
    ):
        raise ValueError(f'"{deflator_method=}" not valid')

    # Default to the first method in the list of valid methods for the source
    if deflator_method is None:
        deflator_method = ValidDeflatorMethods[deflator_source][0]

    return deflator_method


def _validate_exchange_source(deflator_method, exchange_source) -> str:
    # Check if the source specified is part of the available exchange source
    if exchange_source is not None and exchange_source not in ValidExchangeSources:
        raise ValueError(f'"{exchange_source=}" not valid')

    # Default to the first source in the list of valid sources
    if exchange_source is None:
        exchange_source = ValidExchangeMethods[deflator_method][0]

    return exchange_source


def _validate_exchange_method(exchange_source, exchange_method) -> str:
    # Check if the method specified is part of the available exchange methods

    if (
        exchange_method is not None
        and exchange_method not in ValidExchangeMethods[exchange_source]
    ):
        raise ValueError(f'"{exchange_method=}" not valid')

    # Default to the first method in the list of valid methods for the source
    if exchange_method is None:
        exchange_method = ValidExchangeMethods[exchange_source][0]

    return exchange_method


def _create_id_col(df: pd.DataFrame, id_type: str, id_column: str) -> pd.DataFrame:
    """Create an id column.

    By default, if a country does not have a DAC deflator, the DAC, Total deflator is used.
    """

    if id_type == "DAC":
        df["id_"] = df[id_column].map(oecd_codes()).fillna("DAC")
    else:
        df = df.pipe(
            to_iso3, codes_col=id_column, target_col="id_", src_classification=id_type
        )

    return df


def deflate(
    df: pd.DataFrame,
    base_year: int,
    deflator_source: str = None,
    deflator_method: str | None = None,
    exchange_source: str | None = None,
    exchange_method: str | None = None,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    id_type: str = "ISO3",
    date_column: str = "date",
    source_column: str = "value",
    target_column: str = "value",
    to_current: bool = False,
    method: str | None = None,
    source: str | None = None,
    iso_column: str | None = None,
    source_col: str | None = None,
    target_col: str | None = None,
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
        deflator_source:{‘oecd_dac’, 'wb', 'imf'}
            The source of the data used to build the deflators. The value (and
            completeness) of the price deflators may change based on the source.
            Additionally, the OECD DAC data is only available for DAC donors.
        deflator_method:{'gdp', 'gdp_linked', 'cpi', 'pcpi', 'pcpie', None}
            The method used to calculate the price deflator:

            For World Bank (source == 'wb'), default is "gdp":

            •'gdp': using GDP deflators.

            •'gdp_linked': a GDP deflator series which has been linked to
            produce a consistent time series to counteract breaks in series
            over time due to changes in base years, sources or methodologies.

            •'cpi': using Consumer Price Index data

            For IMF (source == 'imf'), default is "gdp":

            •'pcpi': Consumer Price Index data

            •'pcpie': end-period Consumer Price Index (e.g. for December each year).

            For OECD DAC (source == 'oecd_dac'), default is "dac_deflator":
            •'dac_deflator': using the OECD DAC deflator

        exchange_source: The source of the exchange rates. If None, the exchange rates
        of the deflator_source will be used.

        exchange_method: The method used to calculate the exchange rates. If None, the
        default exchange method of the exchange_source will be used.

        source_currency: The iso3 code of the source currency. Note that deflators for EU countries
            are only in Euros from the year in which the Euro was adopted. To produce
            deflators only in euros, use 'emu'.

        target_currency :The iso3 code of the deflated amounts. It can be the same as the source
            currency. In cases where they are different, the exchange rate will be
            applied. To produce deflators only in euros, use 'emu'.

        id_column: The column containing the id codes (iso3 codes, for example) of the data's
        currency.

        id_type:The classification type for the id_column. By default, ISO3 but others are possible.
            Any options used in the Country Converter package are valid. For the OECD DAC
            classification, use 'DAC'.

        date_column:The column containing the date values. The column can contain years (int)
            or datetime objects.

        source_column:The column containing the data to be deflated.

        target_column: Column where the deflated data will be stored. It can be the same as the
            source column if a copy of the original isn't needed.

        to_current: If True, amounts will be treated as in constant prices and converted to
        current prices.

        iso_column:Provided for backwards compatibility. An alias for id_column
        source: Provided for backwards compatibility. An alias for deflator_source
        method: Provided for backwards compatibility. An alias for deflator_method
        source_col: Provided for backwards compatibility. An alias for source_column
        target_col: Provided for backwards compatibility. An alias for target_column

    Returns:
        A pandas DataFrame containing the deflated data. Years for which there
        are no deflators will be returned as null values.


    """

    # ------------------ Backwards compatibility ------------------

    # Backwards compatibility: if the iso_column parameter is used, reassign it
    if iso_column is not None:
        id_column = iso_column
        logger.warning("iso_column is deprecated. Use id_column instead.")

    # Backwards compatibility: if the source parameter is used, reassign it
    if deflator_source is None and source is not None:
        deflator_source = source
        logger.warning("source is deprecated. Use deflator_source instead.")

    # Backwards compatibility: if the method parameter is used, reassign it
    if method is not None:
        deflator_method = method
        logger.warning("method is deprecated. Use deflator_method instead.")

    # Backwards compatibility: if the source_col parameter is used, reassign it
    if source_col is not None:
        source_column = source_col
        logger.warning("source_col is deprecated. Use source_column instead.")

    # Backwards compatibility: if the target_col parameter is used, reassign it
    if target_col is not None:
        target_column = target_col
        logger.warning("target_col is deprecated. Use target_column instead.")

    # -------------------------- Validation -----------------------------
    deflator_source = _validate_deflator_source(deflator_source=deflator_source)

    deflator_method = _validate_deflator_method(
        deflator_source=deflator_source, deflator_method=deflator_method
    )

    exchange_source = _validate_exchange_source(
        deflator_method=exchange_method, exchange_source=exchange_source
    )

    exchange_method = _validate_exchange_method(
        exchange_source=exchange_source, exchange_method=exchange_method
    )

    # ----------------------------- Set up ---------------------------

    # copy the dataframe to avoid modifying the original
    df = df.copy(deep=True)

    # Keep track of original columns to return data in the same order.
    if target_column not in df.columns:
        cols = [*df.columns, target_column]
    else:
        cols = df.columns

    # check if date format matches
    df, year_as_number = check_year_as_number(df=df, date_column=date_column)

    # create id_column
    df = _create_id_col(df=df, id_column=id_column, id_type=id_type)

    # ----------------------------- Load deflator data ---------------------------
    deflator = (
        Deflator(
            base_year=base_year,
            exchange_obj=ExchangeSources[exchange_source][exchange_method],
            deflator_obj=DeflatorSources[deflator_source](),
            deflator_method=deflator_method,
            source_currency=source_currency,
            target_currency=target_currency,
            to_current=to_current,
        )
        .get_deflator()
        .rename(columns={"iso_code": "id_", "year": date_column})
    )

    # ----------------------------- Deflate ---------------------------
    # Merge the original data with the deflator DataFrame
    df = df.merge(
        deflator,
        on=["id_", date_column],
        how="left",
        suffixes=("", "_"),
    )

    # If the reverse option is used, multiply the data. Else divide.
    df[target_column] = df[source_column] / (df.deflator / 100)

    # Keep only the columns present in the original DataFrame (including order)
    df = df.filter(cols, axis=1)

    # If the year is passed as a number, convert it back to a number.
    if year_as_number:
        df[date_column] = df[date_column].dt.year

    return df
