from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from oda_reader import scan

from pydeflate.cache import CacheEntry, bulk_cache_manager
from pydeflate.exceptions import DataSourceError
from pydeflate.sources.common import (
    add_pydeflate_iso3,
    compute_exchange_deflator,
    enforce_pyarrow_types,
    prefix_pydeflate_to_columns,
)

logger = logging.getLogger(__name__)

# The DAC1 columns the DAC pipeline reads, as `oda_reader.scan("dac1")` names them.
DAC1_COLUMNS = [
    "donor_code",
    "donor_name",
    "aidtype_code",
    "flows_code",
    "amounttype_code",
    "year",
    "value",
]

# Total ODA (net disbursements before 2018, grant equivalents from 2018).
_ODA_LINES = [1010, 11010]
_ODA_FLOWS = [1140, 1160]

# DAC1 donors whose pydeflate code is fixed by their DAC code. Name matching
# misses the bulk file's names for some ("G7 Countries, Total").
_DAC_CODE_TO_PYDEFLATE = {918: "EUI", 20001: "DAC", 20003: "G7C"}


def read_dac1_rows(path: str | Path) -> pd.DataFrame:
    """Read the total ODA rows the DAC pipeline needs from a DAC1 Parquet file.

    Args:
        path: A DAC1 table in the layout `oda_reader.scan("dac1")` writes.

    Raises:
        DataSourceError: If the file lacks one of `DAC1_COLUMNS`.
    """
    missing = sorted(set(DAC1_COLUMNS) - set(pq.read_schema(path).names))
    if missing:
        raise DataSourceError(
            f"DAC1 table {path} lacks columns {missing}. Pass the Parquet file "
            "oda_reader.scan('dac1') returns.",
            source="DAC",
        )
    return pd.read_parquet(
        path,
        columns=DAC1_COLUMNS,
        filters=[("aidtype_code", "in", _ODA_LINES), ("flows_code", "in", _ODA_FLOWS)],
    )


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
    """Derive exchange rates as national-currency over USD amounts.

    DAC aggregates publish no national-currency amounts, so their rate falls back
    to 1 (USD).
    """

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


def _set_aggregate_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Set the pydeflate code of DAC aggregates and EU Institutions by DAC code."""

    fixed = df["donor_code"].map(_DAC_CODE_TO_PYDEFLATE)
    df["pydeflate_iso3"] = fixed.where(fixed.notna(), df["pydeflate_iso3"])
    return df


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Align donor metadata with pydeflate naming conventions."""

    return df.rename(columns={"donor_code": "entity_code", "donor_name": "entity"})


def dac_source_frame(dac1_rows: pd.DataFrame) -> pd.DataFrame:
    """Derive the DAC source table (deflators and exchange rates) from DAC1 rows.

    The DAC deflator is ``100 * A / D`` and the exchange rate ``N / A``, read from
    total ODA: line 1010 net disbursements before 2018 and line 11010 grant
    equivalents from 2018. Both are ratios, so the unit of ``value`` (DAC1 bulk
    files report millions) does not matter.

    Args:
        dac1_rows: DAC1 rows with the `DAC1_COLUMNS`, such as `read_dac1_rows`
            returns.

    Returns:
        The table a DAC `Source` holds, with ``pydeflate_``-prefixed columns.
    """
    return (
        dac1_rows.pipe(_keep_official_definition_only)
        .pipe(_pivot_amount_type)
        .pipe(_compute_exchange)
        .pipe(_compute_dac_deflator)
        .pipe(_keep_useful_columns)
        .pipe(add_pydeflate_iso3, column="donor_name")
        .pipe(_set_aggregate_codes)
        .pipe(_rename_columns)
        .pipe(compute_exchange_deflator, base_year_measure="DAC_DEFLATOR")
        .pipe(_compute_dac_gdp_deflator)
        .pipe(prefix_pydeflate_to_columns)
        .pipe(enforce_pyarrow_types)
        .reset_index(drop=True)
    )


def _download_dac(output_path: Path) -> None:
    """Build the DAC source table from a fresh DAC1 bulk file and cache it.

    The pydeflate cache calls this when its copy is missing, past its TTL, or
    `read_dac(update=True)` forces a rebuild. Each case downloads the current
    bulk file (``refresh=True``), so the rebuilt table is never older than the
    rebuild, whatever copy oda_reader holds.
    """

    logger.info("Downloading DAC1 through oda_reader.scan...")
    table = scan("dac1", refresh=True)
    df = dac_source_frame(read_dac1_rows(table.path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    logger.info("Saved DAC dataset (DAC1 release %s) to %s", table.release, output_path)


_DAC_ENTRY = CacheEntry(
    key="dac_stats",
    filename="dac.parquet",
    fetcher=_download_dac,
    ttl_days=30,
    version="3",  # Bump: built from the DAC1 bulk file read through scan("dac1")
)


def read_dac(update: bool = False) -> pd.DataFrame:
    path = bulk_cache_manager().ensure(_DAC_ENTRY, refresh=update)
    return pd.read_parquet(path)


if __name__ == "__main__":  # pragma: no cover
    read_dac(update=True)
