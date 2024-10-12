from pathlib import Path

import pandas as pd
from imf_reader import weo

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.sources.common import check_file_age, today

# List of WEO indicators of interest
WEO_INDICATORS: list[str] = [
    "NGDP_D",  # Gross domestic product, deflator
    "PCPI",  # Inflation, average consumer prices
    "PCPIE",  # Inflation, end of period consumer prices
    "PCPIEPCH",  # Inflation, end of period consumer prices percentage change
    "PCPIPCH",  # Inflation, average consumer prices percentage change
    "PPPEX",  # Implied PPP conversion rate
    "NGDPD",  # Gross domestic product, current prices USD
    "NGDP",  # Gross domestic product, current prices
]


def _filter_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the data to include only selected WEO indicators.

    Args:
        df (pd.DataFrame): The raw dataframe containing WEO data.

    Returns:
        pd.DataFrame: Filtered dataframe with only the relevant indicators.
    """
    return df.loc[df.CONCEPT_CODE.isin(WEO_INDICATORS)]


def _to_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert OBS_VALUE using the SCALE_CODE multiplier to get proper units.

    Args:
        df (pd.DataFrame): Dataframe with raw observation values.

    Returns:
        pd.DataFrame: Dataframe with scaled observation values.
    """
    df = df.copy()
    df["OBS_VALUE"] = df["OBS_VALUE"] * df["SCALE_CODE"]
    return df


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to more readable and consistent names.

    Args:
        df (pd.DataFrame): Dataframe with original IMF column names.

    Returns:
        pd.DataFrame: Dataframe with cleaned and renamed columns.
    """
    df = df.rename(
        columns={
            "REF_AREA_CODE": "entity_code",
            "REF_AREA_LABEL": "entity",
            "LASTACTUALDATE": "estimates_start_after",
            "TIME_PERIOD": "year",
            "OBS_VALUE": "value",
        }
    )
    # Standardize column names to snake_case
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df


def _keep_useful_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Retain only the columns that are useful for further analysis.

    Args:
        df (pd.DataFrame): Dataframe with cleaned columns.

    Returns:
        pd.DataFrame: Dataframe with only useful columns.
    """
    cols = [
        "year",
        "entity_code",
        "entity",
        "concept_code",
        "estimates_start_after",
        "value",
    ]
    return df[cols]


def download_weo() -> None:
    """Download the WEO data, process it, and save it to a parquet file."""
    logger.info("Downloading the latest WEO data...")

    # Fetch and process the data through a pipeline of transformations
    df = (
        weo.fetch_data()
        .pipe(_filter_indicators)
        .pipe(_to_units)
        .pipe(_clean_columns)
        .pipe(_keep_useful_columns)
    )

    # Get today's date to use as a file suffix
    suffix = today()

    # Save the processed dataframe to parquet format
    df.to_parquet(PYDEFLATE_PATHS.data / f"weo_{suffix}.parquet")

    logger.info(f"Saved WEO data to weo_{suffix}.parquet")


def _find_weo_files_in_path(path: Path) -> list:
    """Find all WEO parquet files in the specified directory.

    Args:
        path (Path): The directory path to search for WEO parquet files.

    Returns:
        list: List of WEO parquet files found in the directory.
    """
    return list(path.glob("weo_*.parquet"))


def read_weo(update: bool = False) -> pd.DataFrame:
    """Read the latest WEO data from parquet files or download fresh data.

    Args:
        update (bool): If True, forces downloading of new WEO data even if files exist.

    Returns:
        pd.DataFrame: The latest WEO data.
    """
    # Find existing WEO files in the data directory
    files = _find_weo_files_in_path(PYDEFLATE_PATHS.data)

    # If no files are found or update is requested, download new data
    if len(files) == 0 or update:
        download_weo()
        files = _find_weo_files_in_path(PYDEFLATE_PATHS.data)

    # If files are found, sort them by age and load the most recent one
    if len(files) > 0:
        files = sorted(files, key=check_file_age)
        latest_file = files[0]

        # Check if the latest file is older than 120 days and log a warning
        if check_file_age(latest_file) > 120:
            logger.warn(
                "The latest WEO data is more than 120 days old.\n"
                "Consider updating by setting update=True in the function call."
            )

        # Read and return the latest parquet file as a dataframe
        logger.info(f"Reading WEO data from {latest_file}")
        return pd.read_parquet(latest_file)
