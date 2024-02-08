import csv
import io
import zipfile as zf

import pandas as pd
import requests
from bs4 import BeautifulSoup as Bs

from pydeflate.core.dtypes import set_default_types
from pydeflate.core.schema import PydeflateSchema, OECD_MAPPING
from pydeflate.pydeflate_config import logger
from pydeflate.utils import oecd_codes


def raw2df(csv_file: csv, sep: str, encoding: str) -> pd.DataFrame:
    """Convert a raw csv to a DataFrame. Check the result if requested"""

    try:
        _ = pd.read_csv(
            csv_file, sep=sep, dtype="str", encoding=encoding, low_memory=False
        )
    except UnicodeError:
        raise pd.errors.ParserError

    unnamed_cols = [c for c in _.columns if "unnamed" in c]

    if len(unnamed_cols) > 3:
        raise pd.errors.ParserError

    if len(_.columns) < 3:
        raise pd.errors.ParserError

    return _


def extract_df(request_content, file_name: str, separator: str) -> pd.DataFrame:
    import copy

    for encoding in ["utf_16", "ISO-8859-1"]:
        try:
            rc = copy.deepcopy(request_content)

            # Read the zipfile
            _ = io.BytesIO(rc)
            raw_csv = zf.ZipFile(_).open(file_name)

            # convert to a dataframe
            return raw2df(csv_file=raw_csv, sep=separator, encoding=encoding)
        except pd.errors.ParserError:
            logger.debug(f"{encoding} not valid")

    raise pd.errors.ParserError


def read_zip_content(request_content: bytes, file_name: str) -> pd.DataFrame:
    """Read the contents of a zip file

    Args:
        request_content: the content of the request
        file_name: the name of the file to read.

    Returns:
        A pandas dataframe with the contents of the file

    """
    try:
        return extract_df(
            request_content=request_content, file_name=file_name, separator=","
        )

    except UnicodeDecodeError:
        return extract_df(
            request_content=request_content, file_name=file_name, separator="|"
        )

    except pd.errors.ParserError:
        return extract_df(
            request_content=request_content, file_name=file_name, separator="|"
        )


def download_bulk_file(url: str) -> bytes:
    """Get zipfile bytes from the webpage

    Args:
        url: the url to download the file from

    Returns:
        The content of the file (bytes)

    """

    # get URL
    response = requests.get(url)

    # parse html
    page = Bs(response.text, "html.parser")
    link = list(page.find_all("a"))[0].attrs["onclick"][15:-3].replace("_", "-")
    link = f"https://stats.oecd.org/FileView2.aspx?IDFile={link}"

    return requests.get(link).content


def filter_official_definition(data: pd.DataFrame) -> pd.DataFrame:
    """Filter the data to only keep the flows which were considered official in a
    given year (net disbursements before 2018, and grant equivalents since)"""

    query = (
        f"({PydeflateSchema.AID_TYPE} == 1010 & {PydeflateSchema.FLOWS} == 1140 & "
        f"{PydeflateSchema.YEAR} <2018 ) | "
        f"({PydeflateSchema.AID_TYPE} == 11010 & {PydeflateSchema.FLOWS} == 1160 &"
        f" {PydeflateSchema.YEAR} >=2018)"
    )

    return data.query(query)


def keep_key_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Drop all unnecessary columns"""

    return data.filter(
        [
            PydeflateSchema.PROVIDER_CODE,
            PydeflateSchema.AMOUNT_TYPE,
            PydeflateSchema.YEAR,
            PydeflateSchema.VALUE,
        ],
        axis=1,
    )


def pivot_prices(data: pd.DataFrame) -> pd.DataFrame:
    """Transform the aid type column, which is just prices, to columns"""

    return data.pivot(
        index=[PydeflateSchema.PROVIDER_CODE, PydeflateSchema.YEAR],
        columns=[PydeflateSchema.AMOUNT_TYPE],
        values=PydeflateSchema.VALUE,
    ).reset_index()


def add_exchange(
    data: pd.DataFrame, lcu: str = "N", current_usd: str = "A"
) -> pd.DataFrame:
    """Calculate an exchange rate column"""

    # N is for national currency, A is for current prices USD
    return data.assign(
        **{
            PydeflateSchema.EXCHANGE: lambda d: round(
                d[lcu] / d[current_usd], 5
            ).fillna(1)
        }
    )


def add_exchange_deflator(data: pd.DataFrame) -> pd.DataFrame:
    # Calculate the base year
    base_year = identify_base_year(df=data)

    # Get the exchange data for that year only
    base_year_exchange = data.loc[
        lambda d: d[PydeflateSchema.YEAR] == base_year,
        [PydeflateSchema.PROVIDER_CODE, PydeflateSchema.EXCHANGE],
    ]

    # Merge the base year exchange data with the year exchange data
    data = data.merge(
        base_year_exchange,
        on=[PydeflateSchema.PROVIDER_CODE],
        how="left",
        suffixes=("", "_base"),
    )

    # Create the exchange deflator
    data[PydeflateSchema.EXCHANGE_DEFLATOR] = (
        data[f"{PydeflateSchema.EXCHANGE}_base"] / data[PydeflateSchema.EXCHANGE]
    )

    return data.drop(columns=[f"{PydeflateSchema.EXCHANGE}_base"])


def add_implied_deflator(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate the deflator implied by the data as a new column"""

    # A is for current USD, D is for constant USD
    return data.assign(
        **{PydeflateSchema.DEFLATOR: lambda d: round(100 * d.A / d.D, 6)}
    )


def add_price_deflator(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate what the price deflator should be, based on the deflator and exchange
    information."""

    data[PydeflateSchema.PRICE_DEFLATOR] = round(
        data[PydeflateSchema.DEFLATOR] * data[PydeflateSchema.EXCHANGE_DEFLATOR] / 100,
        6,
    )

    return data


def add_iso3_codes(data: pd.DataFrame) -> pd.DataFrame:
    """Add iso3 codes column"""

    return data.assign(
        **{
            PydeflateSchema.ISO_CODE: lambda d: d[PydeflateSchema.PROVIDER_CODE].map(
                oecd_codes()
            )
        }
    ).dropna(subset=[PydeflateSchema.ISO_CODE])


def keep_output_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Keep only the required columns for output"""
    return data.filter(
        [
            PydeflateSchema.ISO_CODE,
            PydeflateSchema.PROVIDER_CODE,
            PydeflateSchema.YEAR,
            PydeflateSchema.EXCHANGE,
            PydeflateSchema.EXCHANGE_DEFLATOR,
            PydeflateSchema.PRICE_DEFLATOR,
            PydeflateSchema.INDICATOR,
        ],
        axis=1,
    )


def add_indicator(data: pd.DataFrame) -> pd.DataFrame:
    """Add an indicator column"""
    data[PydeflateSchema.INDICATOR] = "oecd_dac"

    return data


def clean_dac1(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DAC1 to keep only relevant information for deflators and exchange.

    Args:
        df: the dataframe to clean

    Returns:
        A cleaned dataframe
    """

    # Clean the data
    data = (
        df.rename(columns=OECD_MAPPING)
        .pipe(set_default_types)
        .pipe(filter_official_definition)
        .pipe(keep_key_columns)
        .pipe(pivot_prices)
        .pipe(add_iso3_codes)
        .pipe(add_exchange)
        .pipe(add_implied_deflator)
        .pipe(add_exchange_deflator)
        .pipe(add_price_deflator)
        .pipe(add_indicator)
        .pipe(keep_output_columns)
        .pipe(set_default_types)
    )

    return data


def identify_base_year(df: pd.DataFrame) -> int:
    """Looks at the data for a set of donors and tries to deduce the current base year"""
    return (
        df.query(f"{PydeflateSchema.ISO_CODE} in ['FRA','GBR','USA','CAN','DEU','EUI']")
        .groupby([PydeflateSchema.YEAR], dropna=False, observed=True, as_index=False)[
            PydeflateSchema.DEFLATOR
        ]
        .mean(numeric_only=True)
        .round(2)
        .loc[lambda d: d[PydeflateSchema.DEFLATOR] == 100.00, PydeflateSchema.YEAR]
        .item()
    )
