"""Compute GDP-weighted aggregate deflators for country groupings.

This module is grouping-agnostic: it takes a membership resolver function
and a group ISO3 code. Specific group data lives in pydeflate.groups.*.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from pydeflate.pydeflate_config import logger


def compute_group_deflator(
    data: pd.DataFrame,
    price_kind: str,
    group_iso3: str,
    get_members: Callable[[int], list[str]],
    dynamic: bool = False,
    pin_year: int | None = None,
) -> pd.DataFrame:
    """Replace a group's aggregate deflator rows with GDP-weighted member average.

    Args:
        data: Source DataFrame with all countries including group aggregate rows.
        price_kind: Deflator column suffix (e.g., "NGDP_D", "PCPI").
        group_iso3: ISO3 code of the group aggregate row (e.g., "EUR").
        get_members: Function returning member ISO3 codes for a given year.
        dynamic: If True, use year-specific membership. If False, use all-time members.
        pin_year: If set, use this year's membership for all rows (overrides dynamic).

    Returns:
        DataFrame with group aggregate deflator rows replaced.
    """
    deflator_col = f"pydeflate_{price_kind}"
    if deflator_col not in data.columns:
        return data

    members = _select_member_rows(data, get_members, dynamic, pin_year)
    if members.empty:
        logger.warning(
            "No member data found for group '%s'. Falling back to source aggregate.",
            group_iso3,
        )
        return data

    replacements = (
        members.groupby("pydeflate_year", sort=False)
        .apply(
            _weighted_mean,
            deflator_col=deflator_col,
            group_iso3=group_iso3,
            include_groups=False,
        )
        .dropna()
        .round(6)
    )

    if replacements.empty:
        return data

    result = data.copy()
    result[deflator_col] = result[deflator_col].astype("float64[pyarrow]")
    mask = result["pydeflate_iso3"] == group_iso3
    mapped = result.loc[mask, "pydeflate_year"].map(replacements)
    has_value = mapped.notna()
    result.loc[mapped.index[has_value], deflator_col] = mapped[has_value].values
    return result


def _select_member_rows(
    data: pd.DataFrame,
    get_members: Callable[[int], list[str]],
    dynamic: bool,
    pin_year: int | None,
) -> pd.DataFrame:
    """Filter data to rows belonging to group members."""
    if pin_year is not None:
        return data[data["pydeflate_iso3"].isin(get_members(pin_year))]

    if not dynamic:
        # All-time membership via far-future sentinel year
        return data[data["pydeflate_iso3"].isin(get_members(9999))]

    # Dynamic: membership varies by year
    parts = [
        data[
            (data["pydeflate_year"] == year)
            & data["pydeflate_iso3"].isin(get_members(int(year)))
        ]
        for year in data["pydeflate_year"].unique()
    ]
    return pd.concat(parts) if parts else data.iloc[0:0]


def _weighted_mean(
    group: pd.DataFrame, deflator_col: str, group_iso3: str
) -> float:
    """GDP-weighted mean of a deflator column, falling back to equal weights."""
    deflators = group[deflator_col].dropna()
    if deflators.empty:
        return float("nan")

    if "pydeflate_NGDPD" not in group.columns:
        return float(deflators.mean())

    gdp = group.loc[deflators.index, "pydeflate_NGDPD"].dropna()
    if gdp.empty or gdp.sum() <= 0:
        logger.warning(
            "No GDP data for group '%s' members in %s, using equal weights",
            group_iso3,
            group.name,
        )
        return float(deflators.mean())

    weights = gdp / gdp.sum()
    return float((weights * group.loc[weights.index, deflator_col]).sum())
