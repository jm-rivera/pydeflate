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


def _use_implied_dac_rates(
    data: pd.DataFrame,
    pydeflate_data: pd.DataFrame,
    ix: list[str],
    entity_column: str,
    source_codes: bool,
) -> pd.DataFrame:
    """When rates are missing for entities in DAC data, the correct behaviour is to use
    the DAC overall rates"""

    # Assign the DAC code to a temporary column
    data.loc[
        lambda d: ~d[f"temp_{entity_column}"].isin(pydeflate_data[ix[-1]].unique()),
        f"temp_{entity_column}",
    ] = (
        20001 if source_codes else "DAC"
    )

    # Log the fact that implied rates are being used
    flag_missing_pydeflate_data(
        unmatched_data=data.loc[
            lambda d: ~d[f"{entity_column}"].isin(pydeflate_data[ix[-1]].unique())
        ],
        entity_column=entity_column,
        year_column="pydeflate_year",
        using_implied=True,
    )

    return data


def merge_user_and_pydeflate_data(
    data: pd.DataFrame,
    pydeflate_data: pd.DataFrame,
    entity_column: str,
    ix: list[str],
    source_codes: bool = True,
    dac: bool = False,
) -> pd.DataFrame:

    data[f"temp_{entity_column}"] = data[entity_column]

    if dac:
        data = _use_implied_dac_rates(
            data=data,
            pydeflate_data=pydeflate_data,
            ix=ix,
            entity_column=entity_column,
            source_codes=source_codes,
        )

    df_ = data.merge(
        pydeflate_data,
        how="outer",
        left_on=["pydeflate_year", f"temp_{entity_column}"],
        right_on=ix,
        suffixes=("", "_pydeflate"),
        indicator=True,
    ).pipe(enforce_pyarrow_types)

    return df_.drop(columns=[f"temp_{entity_column}"])


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


def flag_missing_pydeflate_data(
    unmatched_data: pd.DataFrame,
    entity_column: str,
    year_column: str,
    using_implied: bool = False,
):
    """Flag data which is present in the input data but missing in pydeflate's data."""
    if unmatched_data.empty:
        return
    missing = (
        unmatched_data.filter([entity_column, year_column])
        .drop_duplicates()
        .groupby(entity_column)[year_column]
        .apply(lambda x: ", ".join(map(str, sorted(x))))
        .to_dict()
    )

    missing_str = "\n".join(f"{entity}: {years}" for entity, years in missing.items())

    # log all missing data
    message = (
        "Using DAC members' rates (given missing data) for:"
        if using_implied
        else "Missing exchange data for:"
    )
    logger.info(f"{message}\n{missing_str}")
