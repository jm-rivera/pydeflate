from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import wbgapi as wb

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.sources.common import (
    enforce_pyarrow_types,
    today,
    compute_exchange_deflator,
    read_data,
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
        .sort_values(by=["economy", "Time"])  # Sort for easier reading
        .drop(columns=["Time"])  # Remove unnecessary column
        .rename(
            columns={
                "economy": "entity_code",
                "Country": "entity",
                "time": "year",
                series: value_name or series,
            }
        )
        .reset_index(drop=True)  # Drop the old index after reset
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
        # Submit all tasks to the executor (downloading indicators in parallel)
        future_to_series = {
            executor.submit(get_wb_indicator, series, value_name): series
            for series, value_name in indicators.items()
        }

        # Collect the results as they complete
        for future in as_completed(future_to_series):
            series = future_to_series[future]
            try:
                df_ = future.result().set_index(["year", "entity_code", "entity"])
                dfs.append(df_)
            except Exception as exc:
                # Log or handle any errors that occur during the download
                logger.warning(f"Error downloading series {series}: {exc}")

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

    df = pd.concat([df, ppp], ignore_index=True)

    return df


def _download_wb(
    indicators: dict, prefix: str = "wb", add_ppp_exchange: bool = False
) -> None:
    """Download multiple World Bank indicators in parallel and save as a parquet file.

    This function fetches all indicators defined in _INDICATORS in parallel, concatenates
    them into a single DataFrame, and saves the result as a parquet file using today's date as a suffix.
    """
    logger.info("Downloading the latest World Bank data...")

    indicators_data = _parallel_download_indicators(indicators=indicators)

    # Concatenate all DataFrames horizontally (by columns)
    df = pd.concat(indicators_data, axis=1).reset_index()

    # cleaning
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

    # Get today's date to use as a file suffix
    suffix = today()

    # Save the DataFrame as a parquet file
    output_path = PYDEFLATE_PATHS.data / f"{prefix}_{suffix}.parquet"
    df.to_parquet(output_path)

    logger.info(f"Saved World Bank data to {prefix}_{suffix}.parquet")


def download_wb() -> None:
    """Download the latest World Bank data."""
    _download_wb(indicators=_INDICATORS, prefix="wb")


def download_wb_lcu_ppp() -> None:
    """Download the latest World Bank data (PPP)."""
    _download_wb(
        indicators=_INDICATORS_LCU_PPP, prefix="wb_lcu_ppp", add_ppp_exchange=True
    )


def download_wb_usd_ppp() -> None:
    """Download the latest World Bank data (PPP)."""
    _download_wb(
        indicators=_INDICATORS_USD_PPP, prefix="wb_usd_ppp", add_ppp_exchange=True
    )


def _find_wb_files_in_path(path: Path) -> list:
    """Find all WB parquet files in the specified directory.

    Args:
        path (Path): The directory path to search for WB parquet files.

    Returns:
        list: List of WB parquet files found in the directory.
    """
    return list(path.glob(f"wb_*.parquet"))


def _find_wb_lcu_ppp_files_in_path(path: Path) -> list:
    """Find all WB PPP parquet files in the specified directory.

    Args:
        path (Path): The directory path to search for WB parquet files.

    Returns:
        list: List of WB parquet files found in the directory.
    """
    return list(path.glob(f"wb_lcu_ppp_*.parquet"))


def _find_wb_usd_ppp_files_in_path(path: Path) -> list:
    """Find all WB PPP parquet files in the specified directory.

    Args:
        path (Path): The directory path to search for WB parquet files.

    Returns:
        list: List of WB parquet files found in the directory.
    """
    return list(path.glob(f"wb_usd_ppp_*.parquet"))


def read_wb(update: bool = False) -> pd.DataFrame:
    """Read the latest World Bank data from parquet files or download fresh data."""
    return read_data(
        file_finder_func=_find_wb_files_in_path,
        download_func=download_wb,
        data_name="World Bank",
        update=update,
    )


def read_wb_lcu_ppp(update: bool = False) -> pd.DataFrame:
    """Read the latest World Bank data from parquet files or download fresh data."""
    return read_data(
        file_finder_func=_find_wb_lcu_ppp_files_in_path,
        download_func=download_wb_lcu_ppp,
        data_name="World Bank",
        update=update,
    )


def read_wb_usd_ppp(update: bool = False) -> pd.DataFrame:
    """Read the latest World Bank data from parquet files or download fresh data."""
    return read_data(
        file_finder_func=_find_wb_usd_ppp_files_in_path,
        download_func=download_wb_usd_ppp,
        data_name="World Bank",
        update=update,
    )


if __name__ == "__main__":
    df_wb = read_wb(False)
    df_usd = read_wb_usd_ppp(False)
    df_lcu = read_wb_lcu_ppp(False)
