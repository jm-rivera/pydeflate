from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import pandas as pd
import wbgapi as wb

from pydeflate.cache import CacheEntry, cache_manager
from pydeflate.pydeflate_config import logger
from pydeflate.sources.common import (
    compute_exchange_deflator,
    enforce_pyarrow_types,
    prefix_pydeflate_to_columns,
)
from pydeflate.utils import emu

_INDICATORS: dict = {
    "NY.GDP.DEFL.ZS": "NGDP_D",  # GDP Deflator (Index)
    "NY.GDP.DEFL.ZS.AD": "NGDP_DL",  # GDP Deflator linked series
    "FP.CPI.TOTL": "CPI",  # Consumer Price Index (CPI)
    "PA.NUS.FCRF": "EXCHANGE",  # Official Exchange Rate
}

_INDICATORS_LCU_PPP: dict = {
    "NY.GDP.DEFL.ZS": "NGDP_D",  # GDP Deflator (Index)
    "NY.GDP.DEFL.ZS.AD": "NGDP_DL",  # GDP Deflator linked series
    "PA.NUS.PPP": "EXCHANGE",  # PPP conversion factor
}

_INDICATORS_USD_PPP: dict = {
    "NY.GDP.DEFL.ZS": "NGDP_D",  # GDP Deflator (Index)
    "NY.GDP.DEFL.ZS.AD": "NGDP_DL",  # GDP Deflator linked series
    "PA.NUS.PPPC.RF": "EXCHANGE",  # PPP conversion factor to market exchange rate
}


def get_wb_indicator(series: str, value_name: str | None = None) -> pd.DataFrame:
    """Fetch a World Bank indicator and transform it into a cleaned DataFrame.

    Args:
        series (str): The World Bank indicator series code.
        value_name (str | None): The column name to assign to the series values.
                                 If None, the series code will be used as the column name.

    Returns:
        pd.DataFrame: DataFrame with entity code, entity name, year, and the indicator values.
    """
    # Fetch the indicator data from World Bank API, clean and structure it
    return (
        wb.data.DataFrame(
            series=series,
            db=2,  # World Development Indicators database
            skipBlanks=True,
            columns="series",
            numericTimeKeys=True,
            labels=True,
        )
        .reset_index()
        .sort_values(by=["economy", "Time"])
        .drop(columns=["Time"])
        .rename(
            columns={
                "economy": "entity_code",
                "Country": "entity",
                "time": "year",
                series: value_name or series,
            }
        )
        .reset_index(drop=True)
    )


def _eur_series_fix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix the exchange rate for the Euro area countries. This is done by assigning the
    exchange rate of the Euro to the countries in the Euro area. This is necessary
    because the series for Euro area countries are missing EUR exchange rates.

    Args:
        df: pd.DataFrame: The DataFrame containing the World Bank data.

    Returns:
        pd.DataFrame: The DataFrame with the fixed exchange rates for the Euro area countries.

    """
    # Handle cases where EUR is represented differently in the World Bank data
    df["entity_code"] = df["entity_code"].replace({"EMU": "EUR"})

    # Find the "Euro" data. This is done given that some countries are missing
    # exchange rates, but they are part of the Euro area.
    eur = (
        df.loc[lambda d: d["entity_code"] == "EUR"]
        .dropna(subset=["EXCHANGE"])
        .set_index("year")["EXCHANGE"]
        .to_dict()
    )

    # Euro area countries without exchange rates
    eur_mask = (df["entity_code"].isin(emu())) & (df["EXCHANGE"].isna())

    # Assign EURO exchange rate to euro are countries from year euro adopted
    df.loc[eur_mask, "EXCHANGE"] = df["year"].map(eur)

    return df


def _parallel_download_indicators(indicators: dict) -> list[pd.DataFrame]:
    """Download multiple World Bank indicators in parallel.

    Args:
        indicators (dict): A dictionary of World Bank indicators to download.

    Returns:
        list[pd.DataFrame]: A list of DataFrames containing the downloaded indicators

    """
    # List to store the resulting dataframes
    dfs = []

    # Use ThreadPoolExecutor to fetch indicators in parallel
    with ThreadPoolExecutor() as executor:
        future_to_series = {
            executor.submit(get_wb_indicator, series, value_name): series
            for series, value_name in indicators.items()
        }
        for future in as_completed(future_to_series):
            series = future_to_series[future]
            try:
                df_ = future.result().set_index(["year", "entity_code", "entity"])
                dfs.append(df_)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Error downloading series %s: %s", series, exc)
    return dfs


def _add_ppp_ppp_exchange(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the PPP exchange rate to the DataFrame.

    Args:
        df: pd.DataFrame: The DataFrame containing the World Bank data.

    Returns:
        pd.DataFrame: The DataFrame with the PPP exchange rates

    """
    ppp = df.loc[lambda d: d["entity_code"] == "USA"].copy()
    ppp[["entity_code", "entity", "pydeflate_iso3"]] = "PPP"
    return pd.concat([df, ppp], ignore_index=True)


def _download_wb_dataset(
    indicators: dict, output_path: Path, add_ppp_exchange: bool = False
) -> None:
    """Download and materialise a World Bank dataset to ``output_path``."""

    logger.info("Downloading World Bank indicators for %s", output_path.name)
    indicators_data = _parallel_download_indicators(indicators)
    df = pd.concat(indicators_data, axis=1).reset_index()
    df = (
        df.pipe(_eur_series_fix)
        .pipe(compute_exchange_deflator, base_year_measure="NGDP_D")
        .assign(pydeflate_iso3=lambda d: d.entity_code)
        .sort_values(by=["year", "entity_code"])
    )
    if add_ppp_exchange:
        df = df.pipe(_add_ppp_ppp_exchange)
    df = (
        df.pipe(prefix_pydeflate_to_columns)
        .pipe(enforce_pyarrow_types)
        .reset_index(drop=True)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    logger.info("Saved World Bank data to %s", output_path)


def _entry(
    key: str, filename: str, fetcher: Callable[[Path], None], ttl_days: int = 30
) -> CacheEntry:
    return CacheEntry(key=key, filename=filename, fetcher=fetcher, ttl_days=ttl_days)


_WB_ENTRY = _entry(
    "world_bank", "wb.parquet", lambda p: _download_wb_dataset(_INDICATORS, p)
)
_WB_LCU_PPP_ENTRY = _entry(
    "world_bank_lcu_ppp",
    "wb_lcu_ppp.parquet",
    lambda p: _download_wb_dataset(_INDICATORS_LCU_PPP, p, add_ppp_exchange=True),
)
_WB_USD_PPP_ENTRY = _entry(
    "world_bank_usd_ppp",
    "wb_usd_ppp.parquet",
    lambda p: _download_wb_dataset(_INDICATORS_USD_PPP, p, add_ppp_exchange=True),
)


def read_wb(update: bool = False) -> pd.DataFrame:
    path = cache_manager().ensure(_WB_ENTRY, refresh=update)
    return pd.read_parquet(path)


def read_wb_lcu_ppp(update: bool = False) -> pd.DataFrame:
    path = cache_manager().ensure(_WB_LCU_PPP_ENTRY, refresh=update)
    return pd.read_parquet(path)


def read_wb_usd_ppp(update: bool = False) -> pd.DataFrame:
    path = cache_manager().ensure(_WB_USD_PPP_ENTRY, refresh=update)
    return pd.read_parquet(path)


if __name__ == "__main__":  # pragma: no cover
    read_wb(update=True)
