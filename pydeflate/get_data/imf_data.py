#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import Union

import pandas as pd
from weo import WEO, all_releases, download

from pydeflate import utils
from pydeflate.config import paths


def __check_weo_parameters(
    latest_y: Union[int, None] = None, latest_r: Union[int, None] = None
) -> (int, int):

    """Check parameters and return max values or provided input"""
    if latest_y is None:
        latest_y = max(*all_releases())[0]

    # if latest release isn't provided, take max value
    if latest_r is None:
        latest_r = max(*all_releases())[1]

    return latest_y, latest_r


def _update_weo(latest_y: int = None, latest_r: int = None) -> None:
    """Update data from the World Economic Outlook, using WEO package"""

    latest_y, latest_r = __check_weo_parameters(latest_y, latest_r)

    # Download the file from the IMF website and store in directory
    download(
        latest_y,
        latest_r,
        directory=paths.data,
        filename=f"weo{latest_y}_{latest_r}.csv",
    )
    utils.update_update_date("imf")


def _load_weo(
    latest_y: Union[int, None] = None, latest_r: Union[int, None] = None
) -> pd.DataFrame:
    """loading WEO as a clean dataframe"""

    latest_y, latest_r = __check_weo_parameters(latest_y, latest_r)

    names = {
        "ISO": "iso_code",
        "WEO Subject Code": "indicator",
        "Subject Descriptor": "indicator_name",
        "Units": "units",
        "Scale": "scale",
    }
    to_drop = [
        "WEO Country Code",
        "Country",
        "Subject Notes",
        "Country/Series-specific Notes",
        "Estimates Start After",
    ]

    df = WEO(paths.data + fr"/weo{latest_y}_{latest_r}.csv").df

    return (
        df.drop(to_drop, axis=1)
        .rename(columns=names)
        .melt(id_vars=names.values(), var_name="date", value_name="value")
        .assign(
            year=lambda d: pd.to_datetime(d.date, format="%Y"),
            value=lambda d: d.value.apply(utils.clean_number),
        )
        .dropna(subset=["value"])
        .drop("date", axis=1)
        .reset_index(drop=True)
    )


def _get_imf_indicator(indicator: str) -> pd.DataFrame:

    """Get a specified imf indicator from the downloaded WEO file"""

    return (
        _load_weo()
        .loc[lambda d: d.indicator == indicator]
        .filter(["iso_code", "year", "value"], axis=1)
        .sort_values(["iso_code", "year"])
        .reset_index(drop=True)
    )


def get_inflation_acp():
    """Indicator PCPI, Index"""
    return _get_imf_indicator("PCPI")


def get_inflation_epcp():
    """Indicator PCPIE, Index"""
    return _get_imf_indicator("PCPIE")


def get_gdp_deflator():
    """Indicator NGDP_D, index"""
    return _get_imf_indicator("NGDP_D")


def get_implied_ppp_rate():
    """Indicator PPPEX, National currency per international dollar"""
    return _get_imf_indicator("PPPEX")


def available_methods() -> dict:
    return {
        "gdp": get_gdp_deflator,
        "pcpi": get_inflation_acp,
        "pcpie": get_inflation_epcp,
    }


if __name__ == "__main__":
    pass
