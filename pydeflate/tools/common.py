from __future__ import annotations

import pandas as pd

from pydeflate.core.schema import PydeflateSchema
from pydeflate.pydeflate_config import DEFAULT_BASE


def rebase(
    data: pd.DataFrame, new_base_year: int, deflator_column: str
) -> pd.DataFrame:
    """Change the existing base to a new base. It will take the most recent value which
    is 1 and divide all other values by that value."""

    base_deflator = data.loc[
        lambda d: d[PydeflateSchema.YEAR] == new_base_year,
        [PydeflateSchema.ISO_CODE, deflator_column],
    ]

    # Merge the base year data with the data
    data = data.merge(
        base_deflator,
        on=[PydeflateSchema.ISO_CODE],
        how="left",
        suffixes=("", "_base"),
    )

    # rebase the deflator values
    data[deflator_column] = data[deflator_column] / data[f"{deflator_column}_base"]

    return data.drop(columns=[f"{deflator_column}_base"])


def year_to_int(data: pd.DataFrame) -> pd.DataFrame:
    """Convert year to int"""
    data[PydeflateSchema.YEAR] = data[PydeflateSchema.YEAR].dt.year

    return data


def add_exchange_deflator(data: pd.DataFrame) -> pd.DataFrame:
    # Define the base year as the latest year in the data

    # Get the exchange data for that year only
    base_year_exchange = data.loc[
        lambda d: d[PydeflateSchema.YEAR] == DEFAULT_BASE,
        [PydeflateSchema.ISO_CODE, PydeflateSchema.EXCHANGE],
    ]

    # Merge the base year exchange data with the year exchange data
    data = data.merge(
        base_year_exchange,
        on=[PydeflateSchema.ISO_CODE],
        how="left",
        suffixes=("", "_base"),
    )

    # Create the exchange deflator
    data[PydeflateSchema.EXCHANGE_DEFLATOR] = (
        data[f"{PydeflateSchema.EXCHANGE}_base"] / data[PydeflateSchema.EXCHANGE]
    )

    return data.drop(columns=[f"{PydeflateSchema.EXCHANGE}_base"])
