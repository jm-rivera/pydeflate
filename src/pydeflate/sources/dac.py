from __future__ import annotations

from pathlib import Path

import pandas as pd
from oda_reader import download_dac1

from pydeflate.cache import CacheEntry, cache_manager
from pydeflate.pydeflate_config import logger
from pydeflate.sources.common import (
    add_pydeflate_iso3,
    compute_exchange_deflator,
    enforce_pyarrow_types,
    prefix_pydeflate_to_columns,
)


def _to_units(df: pd.DataFrame) -> pd.DataFrame:
    """Scale reported DAC values (supplied in millions) into base units."""

    df = df.copy()
    df["value"] = df["value"] * df["unit_multiplier"]
    return df


def _keep_official_definition_only(df: pd.DataFrame) -> pd.DataFrame:
    """Retain rows matching the official DAC definition across regime changes."""

    query = (
        "(aidtype_code == 1010 & flows_code == 1140 & year <2018 ) | "
        "(aidtype_code == 11010 & flows_code == 1160 & year >=2018)"
    )
    return df.query(query)


def _keep_useful_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select the key columns used downstream in pydeflate."""

    return df.filter(["year", "donor_code", "donor_name", "EXCHANGE", "DAC_DEFLATOR"])


def _pivot_amount_type(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot amount-type codes into separate columns (A/N/D)."""

    df = df.filter(["year", "donor_code", "donor_name", "amounttype_code", "value"])
    return df.pivot(
        index=[c for c in df.columns if c not in {"amounttype_code", "value"}],
        columns="amounttype_code",
        values="value",
    ).reset_index()


def _compute_exchange(df: pd.DataFrame) -> pd.DataFrame:
    """Derive exchange rates, forcing DAC aggregates to unity."""

    df.loc[lambda d: d.donor_code >= 20000, "N"] = df.loc[
        lambda d: d.donor_code >= 20000, "A"
    ]
    df["EXCHANGE"] = round(df["N"] / df["A"], 6).fillna(1)
    return df


def _compute_dac_deflator(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the published DAC price deflator from amounts A/D."""

    df["DAC_DEFLATOR"] = round(100 * df["A"] / df["D"], 6)
    return df


def _compute_dac_gdp_deflator(df: pd.DataFrame) -> pd.DataFrame:
    """Back out a GDP-style deflator using the exchange deflator."""

    df["NGDP_D"] = round(df["EXCHANGE_D"] / 100 * df["DAC_DEFLATOR"], 5)
    return df


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Align donor metadata with pydeflate naming conventions."""

    return df.rename(columns={"donor_code": "entity_code", "donor_name": "entity"})


def _download_dac(output_path: Path) -> None:
    """Download and cache the DAC statistics parquet file."""

    logger.info("Downloading DAC statistics from ODA reader...")
    df = download_dac1(
        filters={"measure": ["1010", "11010"], "flow_type": ["1140", "1160"]}
    )
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    logger.info("Saved DAC dataset to %s", output_path)


_DAC_ENTRY = CacheEntry(
    key="dac_stats",
    filename="dac.parquet",
    fetcher=_download_dac,
    ttl_days=30,
)


def read_dac(update: bool = False) -> pd.DataFrame:
    path = cache_manager().ensure(_DAC_ENTRY, refresh=update)
    return pd.read_parquet(path)


if __name__ == "__main__":  # pragma: no cover
    read_dac(update=True)
