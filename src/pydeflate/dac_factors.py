"""Conversion factors derived from a DAC1 table the caller supplies."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from oda_reader import ScannedTable

from pydeflate.core.api import BaseDeflate, BaseExchange
from pydeflate.core.source import Source
from pydeflate.sources.dac import dac_source_frame, read_dac1_rows

DAC_TOTAL_CODE = 20001
"""DAC1 code of "DAC Countries, Total", whose factors stand in for missing donors."""

_ENTITY = "pydeflate_entity_code"
_YEAR = "pydeflate_year"


@dataclass(frozen=True)
class DacConversionFactors:
    """Conversion factors for DAC entity-year keys and the DAC1 release behind them.

    Attributes:
        factors: One row per requested entity and year, with columns
            ``entity_code`` (int64), ``year`` (int64), ``factor`` (float64) and
            ``fallback`` (bool). Multiply a value in current US dollars by
            ``factor`` to convert it. ``factor`` is NaN when the table has no
            rate for that year. ``fallback`` is True for an entity absent from
            the table, whose factor is the DAC total's (code 20001).
        release: The release token of the DAC1 table, as
            `oda_reader.ScannedTable.release` reports it, or None when the table
            was passed as a plain path.
    """

    factors: pd.DataFrame
    release: str | None


def get_oecd_dac_conversion_factors(
    dac1: ScannedTable | str | Path,
    *,
    entities: Iterable[int],
    years: Iterable[int],
    target_currency: str = "USA",
    base_year: int | None = None,
) -> DacConversionFactors:
    """Return factors that convert current US dollars, read from the given DAC1 table.

    The factors follow `oecd_dac_exchange` (current prices) and `oecd_dac_deflate`
    (constant prices) with ``source_currency="USA"`` and
    ``use_source_codes=True``: a current-USD value times ``factor`` equals what
    those functions return for it. Deflators and exchange rates come from total
    ODA in the table (line 1010 net disbursements before 2018, line 11010 grant
    equivalents from 2018), so factors and ODA figures read from one table share
    one DAC1 release. Nothing is cached; each call reads the table.

    Args:
        dac1: The DAC1 table, as the `ScannedTable` `oda_reader.scan("dac1")`
            returns or the path of a Parquet file with the same columns.
        entities: DAC donor codes, such as 4 (France) or 918 (EU Institutions).
            Codes absent from the table use the DAC total's factors.
        years: Years to return factors for.
        target_currency: Currency to convert to, as an ISO3 country code or
            ``"USD"``, ``"EUR"``, ``"GBP"``, ``"JPY"`` or ``"CAD"``.
        base_year: None for current prices; otherwise the year whose prices the
            factors convert to.

    Returns:
        DacConversionFactors: The factors for every combination of ``entities``
            and ``years``, sorted by entity and year, and the DAC1 release.

    Raises:
        DataSourceError: If the table lacks a DAC1 column the factors need.
        ValueError: If ``base_year`` is not an int, or the table has no rate for
            ``target_currency`` or no data for ``base_year``.

    Example:
        >>> import oda_reader
        >>> result = get_oecd_dac_conversion_factors(
        ...     oda_reader.scan("dac1"),
        ...     entities=[4, 302],
        ...     years=range(2020, 2024),
        ...     target_currency="EUR",
        ...     base_year=2022,
        ... )
        >>> result.factors.columns.tolist()
        ['entity_code', 'year', 'factor', 'fallback']
    """
    if base_year is not None and (
        not isinstance(base_year, int) or isinstance(base_year, bool)
    ):
        raise ValueError(f"base_year must be an int or None, got {base_year!r}.")

    if isinstance(dac1, ScannedTable):
        path, release = dac1.path, dac1.release
    else:
        path, release = Path(dac1), None

    frame = dac_source_frame(read_dac1_rows(path))
    source = Source(name="DAC", reader=lambda _update: frame)
    rates = _factor_table(source, target_currency=target_currency, base_year=base_year)

    keys = pd.MultiIndex.from_product(
        [sorted({int(e) for e in entities}), sorted({int(y) for y in years})],
        names=["entity_code", "year"],
    ).to_frame(index=False)
    keys["fallback"] = ~keys["entity_code"].isin(rates["entity_code"])
    keys["lookup"] = keys["entity_code"].where(~keys["fallback"], DAC_TOTAL_CODE)

    factors = keys.merge(
        rates.rename(columns={"entity_code": "lookup"}),
        on=["lookup", "year"],
        how="left",
        validate="many_to_one",
    )
    factors = factors[["entity_code", "year", "factor", "fallback"]].astype(
        {"entity_code": "int64", "year": "int64", "factor": "float64"}
    )
    return DacConversionFactors(factors=factors, release=release)


def _factor_table(
    source: Source, *, target_currency: str, base_year: int | None
) -> pd.DataFrame:
    """Factors per entity code and year that the table has rates for.

    The rows match the table `oecd_dac_exchange` or `oecd_dac_deflate` merges
    user data against, so an entity counts as present exactly when those
    functions would find it.
    """
    if base_year is None:
        data = BaseExchange(
            exchange_source=source,
            source_currency="USA",
            target_currency=target_currency,
            use_source_codes=True,
        ).pydeflate_data
        factor = _as_float(data["pydeflate_EXCHANGE"])
    else:
        data = BaseDeflate(
            deflator_source=source,
            exchange_source=source,
            base_year=base_year,
            price_kind="NGDP_D",
            source_currency="USA",
            target_currency=target_currency,
            use_source_codes=True,
        ).pydeflate_data
        factor = 1 / _as_float(data["pydeflate_deflator"])

    return pd.DataFrame(
        {
            "entity_code": data[_ENTITY].astype("int64").to_numpy(),
            "year": data[_YEAR].astype("int64").to_numpy(),
            "factor": factor,
        }
    )


def _as_float(series: pd.Series) -> np.ndarray:
    return series.to_numpy(dtype="float64", na_value=np.nan)
