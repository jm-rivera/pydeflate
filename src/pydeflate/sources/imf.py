from pathlib import Path

import pandas as pd
from imf_reader import weo

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.sources.common import (
    today,
    add_pydeflate_iso3,
    enforce_pyarrow_types,
    compute_exchange_deflator,
    read_data,
    prefix_pydeflate_to_columns,
)

# List of WEO indicators of interest
WEO_INDICATORS: list[str] = [
    "NGDP_D",  # Gross domestic product, deflator
    "PCPI",  # Inflation, average consumer prices
    "PCPIE",  # Inflation, end of period consumer prices
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
        "value",
    ]
    return df[cols]


def _pivot_concept_code(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot the concept code column to get a wide format for the data.

    Args:
        df (pd.DataFrame): Dataframe with concept code column.

    Returns:
        pd.DataFrame: Dataframe with concept code pivoted to columns.
    """
    return df.pivot(
        index=[c for c in df.columns if c not in ["concept_code", "value"]],
        columns="concept_code",
        values="value",
    ).reset_index()


def _compute_exchange(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the exchange rate and append it to the original DataFrame.

    This function calculates the exchange rate by dividing the 'NGDP'
     Gross domestic product in local currency) by 'NGDPD' (Gross domestic product in USD).
    It then appends this computed exchange rate to the original DataFrame,
    and the new exchange rate rows are labeled with the 'EXCHANGE'
    concept code.

    Args:
        df (pd.DataFrame): Input DataFrame containing columns with
        'concept_code' as 'NGDPD' and 'NGDP'.

    Returns:
        pd.DataFrame: DataFrame with the computed exchange rate included,
        along with the original data.
    """
    # Filter rows with 'NGDPD' (GDP in USD) and 'NGDP' (GDP in local currency)
    exchange = df.loc[lambda d: d.concept_code.isin(["NGDPD", "NGDP"])]

    # Pivot the data so 'NGDPD' and 'NGDP' become separate columns
    exchange = exchange.pipe(_pivot_concept_code)

    # Remove rows that correspond to 'NGDPD' and 'NGDP' from the original DataFrame
    df = df.loc[lambda d: ~d.concept_code.isin(["NGDPD", "NGDP"])]

    # Compute the exchange rate as NGDP (local currency) divided by NGDPD (USD)
    exchange["value"] = round(exchange["NGDP"] / exchange["NGDPD"], 7)

    # Label the exchange rate with a new concept code 'EXCHANGE'
    exchange["concept_code"] = "EXCHANGE"

    # Drop the original 'NGDPD' and 'NGDP' columns as they are no longer needed
    exchange = exchange.drop(columns=["NGDPD", "NGDP"])

    # Concatenate the original DataFrame with the new exchange rate data
    return pd.concat([df, exchange], ignore_index=True)


def _create_eur_series(df: pd.DataFrame) -> pd.DataFrame:
    """Create a EUR series from the exchange rate data.

    This function creates exchange rate data for EUR by using the exchange rate
    from France starting from 1999.

     Args:
         df (pd.DataFrame): DataFrame containing exchange rates.

     Returns:
         pd.DataFrame: DataFrame with the EUR exchange rate.
    """

    # Get France's exchange rates by year
    eur = (
        df.loc[lambda d: d.pydeflate_iso3 == "FRA"]
        .loc[lambda d: d.year >= 1999]
        .set_index("year")["EXCHANGE"]
    )

    # Apply France's exchange rates to rows with entity_code == 998 and matching year
    df.loc[df.entity_code == 998, "EXCHANGE"] = df.loc[
        df.entity_code == 998, "year"
    ].map(eur)

    return df


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
        .pipe(_compute_exchange)
        .pipe(add_pydeflate_iso3, column="entity", from_type="regex")
        .pipe(_pivot_concept_code)
        .pipe(_create_eur_series)
        .pipe(compute_exchange_deflator, base_year_measure="NGDP_D")
        .pipe(prefix_pydeflate_to_columns)
        .pipe(enforce_pyarrow_types)
        .reset_index(drop=True)
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
    """Read the latest WEO data from parquet files or download fresh data."""
    return read_data(
        file_finder_func=_find_weo_files_in_path,
        download_func=download_weo,
        data_name="WEO",
        update=update,
    )


if __name__ == "__main__":
    # Download the WEO data
    dfi = read_weo(update=True)
