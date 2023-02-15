import json

import country_converter as coco
import numpy as np
import pandas as pd

from pydeflate.pydeflate_config import PYDEFLATE_PATHS


def oecd_codes() -> dict:
    with open(PYDEFLATE_PATHS.settings / "oecd_codes.json") as file:
        updates = json.load(file)

    return {int(k): v for k, v in updates.items()}


def emu() -> list:
    with open(PYDEFLATE_PATHS.settings / "emu.json") as file:
        emu = json.load(file)

    return emu


def clean_number(number):
    """Clean a number and return as float"""
    import re

    if not isinstance(number, str):
        number = str(number)

    number = re.sub(r"[^\d.]", "", number)

    if number == "":
        return np.nan

    return float(number)


def check_year_as_number(df: pd.DataFrame, date_column: str) -> (pd.DataFrame, bool):
    """Check whether the date column contains an int instead of datetime.
    This changes the column to datetime and returns a flag"""

    if pd.api.types.is_numeric_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column], format="%Y")
        year_as_number = True
    else:
        year_as_number = False

    return df, year_as_number


def to_iso3(
    df: pd.DataFrame,
    codes_col: str,
    target_col: str,
    src_classification: str | None = None,
    not_found: str | None = None,
) -> pd.DataFrame:
    """Convert a column of country codes to iso3"""

    cc = coco.CountryConverter()

    df[target_col] = cc.pandas_convert(
        df[codes_col], src=src_classification, to="ISO3", not_found=not_found
    )

    return df
