#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime

import requests_cache

from pydeflate import config

# Create session
expire_after = datetime.timedelta(days=3)

wb_session = requests_cache.CachedSession(
    cache_name=config.paths.data + r"/wb_cache",
    backend="sqlite",
    expire_after=expire_after,
)


import pandas as pd
from pandas_datareader import wb

from pydeflate.utils import emu, value_index, update_update_date


def get_iso3c():
    countries = wb.get_countries(session=wb_session)
    return countries[["name", "iso3c"]].set_index("name")["iso3c"].to_dict()


def _download_wb_indicator(indicator: str, start: int, end: int) -> None:

    """Download an indicator from WB (caching if applicable)"""

    df = (
        wb.WorldBankReader(
            symbols=indicator,
            countries="all",
            start=start,
            end=end,
            session=wb_session,
        )
        .read()
        .reset_index(drop=False)
    )

    df.to_feather(config.paths.data + rf"/{indicator}_{start}_{end}.feather")
    print(f"Successfully updated {indicator} for {start}-{end}")
    update_update_date("wb")


def _read_wb_indicator(indicator: str, start: int, end: int) -> pd.DataFrame:

    """Read an indicator from WB"""
    return pd.read_feather(config.paths.data + rf"/{indicator}_{start}_{end}.feather")


def _clean_wb_indicator(
    data: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:

    """Add iso_code, change value name to value and sort"""

    return (
        data.assign(
            iso_code=lambda d: d.country.map(get_iso3c()),
            year=lambda d: pd.to_datetime(d.year, format="%Y"),
        )
        .rename(columns={indicator: "value"})
        .dropna(subset=["iso_code"])
        .sort_values(["iso_code", "year"])
        .reset_index(drop=True)
        .filter(["year", "iso_code", "value"], axis=1)
    )


def wb_indicator(indicator: str, start: int = 1950, end: int = 2025) -> pd.DataFrame:

    """Download and clean an indicator from the WB.
    - indicator: string like 'PA.NUS.FCRF'
    - start: integer with starting year (or closest available)
    - end: integer with ending year (or closest available)
    """

    # Get data object
    data = _read_wb_indicator(indicator=indicator, start=start, end=end)

    # Convert to dataframe and clean
    df = _clean_wb_indicator(data, indicator)

    return df


def update_indicators() -> None:
    """Update data for all WB indicators"""

    indicators = [
        "NY.GDP.DEFL.ZS",
        "NY.GDP.DEFL.ZS.AD",
        "FP.CPI.TOTL",
        "PA.NUS.FCRF",
        "PX.REX.REER",
    ]

    _ = [_download_wb_indicator(i, 1950, 2025) for i in indicators]


def get_gdp_deflator() -> pd.DataFrame:
    """The GDP implicit deflator is the ratio of GDP in current local currency
    to GDP in constant local currency. The base year varies by country."""

    return wb_indicator(indicator="NY.GDP.DEFL.ZS")


def get_gdp_deflator_linked() -> pd.DataFrame:
    """The GDP implicit deflator is calculated as the ratio of GDP in current
    local currency to GDP in constant local currency. This series has been
    linked to produce a consistent time series to counteract breaks in
    series over time due to changes in base years, source data and
    methodologies. Thus, it may not be comparable with other national
    accounts series in the database for historical years. The base year
    varies by country."""

    return wb_indicator(indicator="NY.GDP.DEFL.ZS.AD")


def get_consumer_price_index() -> pd.DataFrame:
    """Consumer price index reflects changes in the cost to the average
    consumer of acquiring a basket of goods and services that may be fixed
    or changed at specified intervals, such as yearly. The Laspeyres formula
    is generally used. Data are period averages."""

    return wb_indicator(indicator="FP.CPI.TOTL")


def get_euro2usd() -> dict:
    """Dictionary of EUR to USD exchange rates"""

    return get_exchange2usd_dict("EMU")


def get_can2usd() -> dict:
    """Dictionary of CAN to USD exchange rates"""

    return get_exchange2usd_dict("CAN")


def get_gbp2usd() -> dict:
    """Dictionary of GBP to USD exchange rates"""

    return get_exchange2usd_dict("GBR")


def get_usd_exchange() -> pd.DataFrame:
    """Official exchange rate refers to the exchange rate determined by
    national authorities or to the rate determined in the legally
    sanctioned exchange market. It is calculated as an annual average based on
    monthly averages (local currency units relative to the U.S. dollar)."""

    # get exchange rates
    df = wb_indicator(indicator="PA.NUS.FCRF")

    eur = df.loc[df.iso_code == "EMU"].dropna().set_index("year")["value"].to_dict()

    # Euro area countries without exchange rates
    eur_mask = (df.iso_code.isin(emu)) & (df.value.isna())

    # Assign EURO exchange rate to euro are countries from year euro adopted
    df.loc[eur_mask, "value"] = df.year.map(eur)

    return df


def get_exchange2usd_dict(currency_iso: str) -> dict:
    """Dictionary of currency_iso to USD"""

    df = get_usd_exchange()

    return (
        df.loc[df.iso_code == currency_iso]
        .dropna()
        .set_index("year")["value"]
        .to_dict()
    )


def get_currency_exchange(currency_iso: str) -> pd.DataFrame:
    """Get exchange rates based on a given currency/country (from LCU)"""
    # Get WB exchange rates
    df = get_usd_exchange()
    target_xe = get_exchange2usd_dict(currency_iso)

    df.value = df.value / df.year.map(target_xe)

    return df


def get_real_effective_exchange_index() -> pd.DataFrame:
    """Real effective exchange rate is the nominal effective exchange rate
    (a measure of the value of a currency against a weighted average of several
     foreign currencies) divided by a price deflator or index of costs."""

    return wb_indicator(indicator="PX.REX.REER")


def get_xe_deflator(currency_iso: str = "USA", base_year: int = 2010) -> pd.DataFrame:
    """get exchange rate deflator based on OECD base year and exchange rates"""

    from datetime import datetime

    # get exchange rates
    xe = get_currency_exchange(currency_iso=currency_iso)

    # get deflators and base year
    base = {iso: datetime(base_year, 1, 1) for iso in xe.iso_code.unique()}

    # get the exchange rate as an index based on the base year
    xe.value = value_index(xe, base)

    return xe


def available_methods() -> dict:
    return {
        "gdp": get_gdp_deflator,
        "gdp_linked": get_gdp_deflator_linked,
        "cpi": get_consumer_price_index,
    }


if __name__ == "__main__":
    pass
