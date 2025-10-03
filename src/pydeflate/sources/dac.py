from pathlib import Path

import pandas as pd
from oda_reader import download_dac1

from pydeflate.pydeflate_config import PYDEFLATE_PATHS
from pydeflate.sources.common import (
    today,
    add_pydeflate_iso3,
    enforce_pyarrow_types,
    compute_exchange_deflator,
    read_data,
    prefix_pydeflate_to_columns,
)


def _find_dac_files_in_path(path: Path) -> list:
    """Find all DAC parquet files in the specified directory.

    Args:
        path (Path): The directory path to search for DAC parquet files.

    Returns:
        list: List of DAC parquet files found in the directory.
    """
    return list(path.glob("dac_*.parquet"))


def _to_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert DAC values (in million) to units.

    Args:
        df (pd.DataFrame): Dataframe with raw observation values.

    Returns:
        pd.DataFrame: Dataframe with scaled observation values.
    """
    df = df.copy()
    df["value"] = df["value"] * df["unit_multiplier"]
    return df


def _keep_official_definition_only(df: pd.DataFrame) -> pd.DataFrame:
    query = (
        "(aidtype_code == 1010 & flows_code == 1140 & year <2018 ) | "
        "(aidtype_code == 11010 & flows_code == 1160 & year >=2018)"
    )

    return df.query(query)


def _keep_useful_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["year", "donor_code", "donor_name", "EXCHANGE", "DAC_DEFLATOR"]

    return df.filter(columns)


def _pivot_amount_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.filter(["year", "donor_code", "donor_name", "amounttype_code", "value"])
    return df.pivot(
        index=[c for c in df.columns if c not in ["amounttype_code", "value"]],
        columns="amounttype_code",
        values="value",
    ).reset_index()


def _compute_exchange(df: pd.DataFrame) -> pd.DataFrame:
    # The values for certain providers should be 1
    df.loc[lambda d: d.donor_code >= 20000, "N"] = df.loc[
        lambda d: d.donor_code >= 20000, "A"
    ]
    df["EXCHANGE"] = round(df["N"] / df["A"], 6).fillna(1)
    return df


def _compute_dac_deflator(df: pd.DataFrame) -> pd.DataFrame:
    df["DAC_DEFLATOR"] = round(100 * df["A"] / df["D"], 6)
    return df


def _compute_dac_gdp_deflator(df: pd.DataFrame) -> pd.DataFrame:
    df["NGDP_D"] = round(df["EXCHANGE_D"] / 100 * df["DAC_DEFLATOR"], 5)

    return df


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "donor_code": "entity_code",
            "donor_name": "entity",
        }
    )


def download_dac():
    # Use oda_reader to get the data
    df = download_dac1(
        filters={"measure": ["1010", "11010"], "flow_type": ["1140", "1160"]}
    )

    # Clean the data
    df = (
        df.pipe(_to_units)
        .pipe(_keep_official_definition_only)
        .pipe(_pivot_amount_type)
        .pipe(_compute_exchange)
        .pipe(_compute_dac_deflator)
        .pipe(_keep_useful_columns)
        .pipe(add_pydeflate_iso3, column="donor_name", from_type="regex")
        .pipe(_rename_columns)
        .pipe(compute_exchange_deflator, base_year_measure="DAC_DEFLATOR")
        .pipe(_compute_dac_gdp_deflator)
        .pipe(prefix_pydeflate_to_columns)
        .pipe(enforce_pyarrow_types)
        .reset_index(drop=True)
    )

    # Get today's date to use as a file suffix
    suffix = today()

    # Save the data
    df.to_parquet(PYDEFLATE_PATHS.data / f"dac_{suffix}.parquet")


def read_dac(update: bool = False) -> pd.DataFrame:
    """Read the latest WEO data from parquet files or download fresh data."""
    return read_data(
        file_finder_func=_find_dac_files_in_path,
        download_func=download_dac,
        data_name="DAC",
        update=update,
    )


if __name__ == "__main__":
    df = read_dac(update=True)
