from __future__ import annotations

from pathlib import Path

import pandas as pd
from imf_reader import weo

from pydeflate.cache import CacheEntry, cache_manager
from pydeflate.pydeflate_config import logger
from pydeflate.sources.common import (
    add_pydeflate_iso3,
    compute_exchange_deflator,
    enforce_pyarrow_types,
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
    """Pivot the concept dimension so each indicator becomes a column

    Args:
        df (pd.DataFrame): Dataframe with concept code column.

    Returns:
        pd.DataFrame: Dataframe with concept code pivoted to columns.
    """
    return df.pivot(
        index=[c for c in df.columns if c not in {"concept_code", "value"}],
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

    # Apply France's exchange rates to Euro Area rows (entity_code G163) with matching year
    # Note: IMF WEO uses "G163" as the entity code for "Euro Area (EA)"
    euro_area_mask = df.entity_code == "G163"
    df.loc[euro_area_mask, "EXCHANGE"] = df.loc[euro_area_mask, "year"].map(eur)
    return df


def _download_weo(output_path: Path) -> None:
    """Fetch, transform, and store the latest WEO dataset in Parquet format."""

    logger.info("Downloading the latest IMF WEO dataset...")
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    logger.info("Saved WEO data to %s", output_path)


_IMF_CACHE_ENTRY = CacheEntry(
    key="imf_weo",
    filename="imf_weo.parquet",
    fetcher=_download_weo,
    ttl_days=60,
    version="2",  # Bump version to invalidate cache when EUR mapping fix is applied
)


def read_weo(update: bool = False) -> pd.DataFrame:
    path = cache_manager().ensure(_IMF_CACHE_ENTRY, refresh=update)
    return pd.read_parquet(path)


if __name__ == "__main__":  # pragma: no cover
    read_weo(update=True)
