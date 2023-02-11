import datetime
import json
import warnings

import country_converter as coco
import numpy as np
import pandas as pd

from pydeflate.pydeflate_config import PYDEFLATE_PATHS

CC = coco.CountryConverter()


def _diff_from_today(date: datetime.datetime):
    """Compare to today"""

    today = datetime.datetime.today()

    return (today - date).days


def warn_updates():

    with open(PYDEFLATE_PATHS.data / "data_updates.json") as file:
        updates = json.load(file)

    for source, date in updates.items():
        d = datetime.datetime.strptime(date, "%Y-%m-%d")
        if _diff_from_today(d) > 50:
            message = (
                f'\n\nThe underlying data for "{source}" has not been updated'
                f" in over {_diff_from_today(d)} days. \nIn order to use"
                " pydeflate with the most recent data, please run:\n"
                "`pydeflate.update_all_data()`"
            )
            warnings.warn(message)


def update_update_date(source: str):
    """Update the most recent update date for data to today"""

    today = datetime.datetime.today().strftime("%Y-%m-%d")

    # Check to see if specified path contains an update file. Create one if not
    if not (PYDEFLATE_PATHS.data / "data_updates.json").exists():
        updates = {}
        with open(PYDEFLATE_PATHS.data / "data_updates.json", "w") as outfile:
            json.dump(updates, outfile)

    with open(PYDEFLATE_PATHS.data / "data_updates.json") as file:
        updates = json.load(file)

    updates[source] = today

    with open(PYDEFLATE_PATHS.data / "data_updates.json", "w") as outfile:
        json.dump(updates, outfile)


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


def base_year_dict(df: pd.DataFrame, date_col: str = "date") -> dict:
    """Return dictionary of base years by iso_code"""

    return df.loc[df.value == 100].set_index("iso_code")[date_col].to_dict()


def value_index(df: pd.DataFrame, base_dict: dict) -> pd.Series:
    """Reindex a series given a base year dictionary"""

    data = df.copy()
    df_ = df.copy()

    df_["base"] = df_.iso_code.map(base_dict)
    df_ = df_.loc[df_.year == df_.base]

    base_values = (
        df_.loc[lambda d: d.value.notna()]
        .round(6)
        .set_index("iso_code")["value"]
        .to_dict()
    )

    return round(100 * data.value / data.iso_code.map(base_values), 6)


def rebase(df_: pd.DataFrame, base_year: int) -> pd.Series:
    """Rebase values to a given base year"""

    base_values = (
        df_.loc[df_.year.dt.year == base_year].set_index("iso_code")["value"].to_dict()
    )

    return round(100 * df_.value / df_.iso_code.map(base_values), 6)


def check_method(method: str, methods: dict):
    """Check whether a given method is in a methods dictionary"""

    if method not in methods.keys():
        raise ValueError(f'Method "{method}" not valid. Please see documentation.')


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
    df[target_col] = CC.pandas_convert(
        df[codes_col], src=src_classification, to="ISO3", not_found=not_found
    )
    return df
