import json

import numpy as np
import pandas as pd

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.sources.common import enforce_pyarrow_types


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

def create_pydeflate_year(
    data: pd.DataFrame, year_column: str, year_format: str | None = None
) -> pd.DataFrame:
    if year_format is None:
        year_format = "ISO8601"

    data = data.copy()

    data["pydeflate_year"] = pd.to_datetime(
        data[year_column], format=year_format
    ).dt.year

    return data


def merge_user_and_pydeflate_data(
    data: pd.DataFrame,
    pydeflate_data: pd.DataFrame,
    entity_column: str,
    ix: list[str],
) -> pd.DataFrame:
    return data.merge(
        pydeflate_data,
        how="outer",
        left_on=["pydeflate_year", entity_column],
        right_on=ix,
        suffixes=("", "_pydeflate"),
        indicator=True,
    ).pipe(enforce_pyarrow_types)


def get_unmatched_pydeflate_data(
    merged_data: pd.DataFrame,
):
    return merged_data.loc[merged_data["_merge"] == "left_only"].filter(
        regex="^(?!pydeflate_)(?!.*_pydeflate$)"
    )


def get_matched_pydeflate_data(
    merged_data: pd.DataFrame,
):
    return (
        merged_data.loc[merged_data["_merge"] != "right_only"]
        .drop(columns="_merge")
        .reset_index(drop=True)
    )


def flag_missing_pydeflate_data(unmatched_data: pd.DataFrame):
    """Flag data which is present in the input data but missing in pydeflate's data."""
    if unmatched_data.empty:
        return

    missing = (
        unmatched_data.drop_duplicates()
        .dropna(axis=1)
        .drop(columns="_merge")
        .to_string(index=False)
    )

    # log all missing data
    logger.info(f"Missing exchange data for:\n {missing}")
