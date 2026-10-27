import json
import logging
import re
import warnings

import numpy as np
import pandas as pd

from pydeflate.pydeflate_config import PYDEFLATE_PATHS
from pydeflate.sources.common import enforce_pyarrow_types

logger = logging.getLogger(__name__)


def oecd_codes() -> dict:
    with open(PYDEFLATE_PATHS.settings / "oecd_codes.json") as file:
        updates = json.load(file)

    return {int(k): v for k, v in updates.items()}


def clean_number(number):
    """Clean a number-like value and return it as a float.

    Preserves leading signs and scientific notation while stripping
    formatting artifacts such as commas or surrounding text.
    """

    if not isinstance(number, str):
        number = str(number)

    normalized = number.replace(",", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", normalized)

    if not match:
        return np.nan

    try:
        return float(match.group())
    except ValueError:
        return np.nan


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

    # Assign the DAC code to a temporary column, matching the dtype of the column
    col = f"temp_{entity_column}"
    dac_code: int | str = 20001 if source_codes else "DAC"
    if pd.api.types.is_string_dtype(data[col]):
        dac_code = str(dac_code)
    data.loc[
        lambda d: ~d[col].isin(pydeflate_data[ix[-1]].unique()),
        col,
    ] = dac_code

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


# DAC1 API codes the DAC1 bulk file numbers differently: EU Institutions.
_LEGACY_DAC_CODES = {20918: 918}


def _translate_legacy_dac_codes(data: pd.DataFrame, entity_column: str) -> None:
    """Look up data keyed by a legacy DAC1 API code under its bulk-file code.

    Rewrites the ``temp_`` lookup column in place, matching its dtype as
    `_use_implied_dac_rates` does. The user's column keeps its codes.
    """
    col = f"temp_{entity_column}"
    as_str = pd.api.types.is_string_dtype(data[col])
    for legacy, current in _LEGACY_DAC_CODES.items():
        old, new = (str(legacy), str(current)) if as_str else (legacy, current)
        mask = data[col] == old
        if not mask.any():
            continue
        data.loc[mask, col] = new
        warnings.warn(
            f"DAC code {legacy} is read as {current}, the code the DAC1 bulk file "
            f"uses. Key your data by {current}: this translation will be removed "
            "in pydeflate 3.0.",
            FutureWarning,
            stacklevel=2,
        )


def merge_user_and_pydeflate_data(
    data: pd.DataFrame,
    pydeflate_data: pd.DataFrame,
    entity_column: str,
    ix: list[str],
    source_codes: bool = True,
    dac: bool = False,
) -> pd.DataFrame:
    data[f"temp_{entity_column}"] = data[entity_column]

    if dac and source_codes:
        _translate_legacy_dac_codes(data, entity_column)

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
