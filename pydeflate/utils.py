#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import warnings

import numpy as np
import pandas as pd

from pydeflate import config


def _diff_from_today(date: datetime.datetime):
    """Compare to today"""

    today = datetime.datetime.today()

    return (today - date).days


def warn_updates():
    with open(config.paths.data + r"/data_updates.json") as file:
        updates = json.load(file)

    for source, date in updates.items():
        d = datetime.datetime.strptime(date, "%Y-%m-%d")
        if _diff_from_today(d) > 50:
            message = (
                f'\n\nThe underlying data for "{source}" has not been updated'
                f" in over {_diff_from_today(d)} days. \nIn order to use"
                " pydeflate with the most recent data, please run:\n"
                '"pydeflate.update_all_data()"\n\n'
            )
            warnings.warn(message)


def update_update_date(source: str):
    """Update the most recent update date for data to today"""

    today = datetime.datetime.today().strftime("%Y-%m-%d")

    with open(config.paths.data + r"/data_updates.json") as file:
        updates = json.load(file)

    updates[source] = today

    with open(config.paths.data + r"/data_updates.json", "w") as outfile:
        json.dump(updates, outfile)


oecd_codes = {
    1: "AUT",
    2: "BEL",
    3: "DNK",
    4: "FRA",
    5: "DEU",
    6: "ITA",
    7: "NLD",
    8: "NOR",
    9: "PRT",
    10: "SWE",
    11: "CHE",
    12: "GBR",
    18: "FIN",
    20: "ISL",
    21: "IRL",
    22: "LUX",
    40: "GRC",
    50: "ESP",
    61: "SVN",
    68: "CZE",
    69: "SVK",
    75: "HUN",
    76: "POL",
    301: "CAN",
    302: "USA",
    701: "JPN",
    742: "KOR",
    801: "AUS",
    820: "NZL",
    918: "EUI",
    30: "CYP",
    45: "MLT",
    55: "TUR",
    62: "HRV",
    70: "LIE",
    72: "BGR",
    77: "ROU",
    82: "EST",
    83: "LVA",
    84: "LTU",
    87: "RUS",
    130: "DZA",
    133: "LBY",
    358: "MEX",
    543: "IRQ",
    546: "ISR",
    552: "KWT",
    561: "QAT",
    566: "SAU",
    576: "ARE",
    611: "AZE",
    613: "KAZ",
    732: "TWN",
    764: "THA",
    765: "TLS",
}


emu = [
    "AUT",
    "BEL",
    "CYP",
    "EST",
    "FIN",
    "FRA",
    "DEU",
    "GRC",
    "IRL",
    "ITA",
    "LVA",
    "LTU",
    "LUX",
    "MLT",
    "NLD",
    "PRT",
    "SVK",
    "SVN",
    "ESP",
]


def clean_number(number):
    """Clean a number and return as float"""
    import re

    if not isinstance(number, str):
        number = str(number)

    number = re.sub(r"[^0-9.]", "", number)

    if number == "":
        return np.nan

    return float(number)


def base_year(df: pd.DataFrame, date_col: str = "date") -> dict:

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
        .round(5)
        .set_index("iso_code")["value"]
        .to_dict()
    )

    return round(100 * data.value / data.iso_code.map(base_values), 3)


def rebase(df_: pd.DataFrame, base_year: int) -> pd.Series:
    """Rebase values to a given base year"""

    base_values = (
        df_.loc[df_.year.dt.year == base_year].set_index("iso_code")["value"].to_dict()
    )

    return round(100 * df_.value / df_.iso_code.map(base_values), 3)


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
