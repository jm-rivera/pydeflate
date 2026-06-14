from __future__ import annotations

import functools
from typing import Any, Literal

import pandas as pd
from resolvekit import Resolver

from pydeflate.pydeflate_config import logger

AvailableDeflators = Literal["NGDP_D", "NGDP_DL", "CPI", "PCPI", "PCPIE"]

# Maps resolvekit entity_ids to pydeflate's own aggregate codes.
# These codes (EU/EMU/EUI/DAC/G7C/SSA/WLD/XXK) are pydeflate policy/inventory
# and don't belong in resolvekit's data. The dict-override check must precede
# the country/ prefix-strip so country/XKS → XXK wins over the iso3 fallback XKX.
ENTITY_TO_PYDEFLATE: dict[str, str] = {
    "EuropeanUnion": "EU",
    "groups/Eurozone": "EMU",
    "DAC/EUInstitutions": "EUI",
    "DAC/DacCountries": "DAC",
    "DAC/DacMembers": "DAC",
    "groups/G7": "G7C",
    "m49/202": "SSA",
    "m49/001": "WLD",
    "country/XKS": "XXK",
}


@functools.cache
def _get_resolver() -> Resolver:
    """Return the process-wide cached resolvekit Resolver (lazy singleton)."""
    return Resolver.lite()


def enforce_pyarrow_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure that a DataFrame uses pyarrow-backed dtypes."""

    return df.convert_dtypes(dtype_backend="pyarrow")


def _match_name_to_iso3(to_match: list[str]) -> dict[str, str | None]:
    """Resolve entity-name strings to pydeflate codes via resolvekit.

    Returns a dict mapping each name to its pydeflate code — ISO3 for country
    entities; aggregate codes (WLD, EU, EMU, EUI, DAC, G7C, SSA, XXK) for
    recognised group entities; None for unresolved names.

    Args:
        to_match: A list of entity name strings to resolve.

    Returns:
        A dict with entity names as keys and pydeflate codes (or None) as values.
    """
    resolver = _get_resolver()
    result: dict[str, str | None] = {}

    for name in to_match:
        entity_id = resolver.resolve_id(name, on_ambiguous="null")
        if entity_id is None:
            result[name] = None
            logger.debug("No ISO3 match found for %s", name)
            continue
        if entity_id in ENTITY_TO_PYDEFLATE:
            # Dict override wins (e.g. country/XKS → XXK beats iso3 XKX)
            result[name] = ENTITY_TO_PYDEFLATE[entity_id]
        elif entity_id.startswith("country/"):
            # Country entity → derive ISO3 from entity_id directly
            result[name] = entity_id.removeprefix("country/")
        else:
            # Aggregate not in dict / unmapped entity system → unresolved
            result[name] = None
            logger.debug("No ISO3 match found for %s", name)

    return result


def convert_id(
    series: pd.Series,
    not_found: Any = None,
) -> pd.Series:
    """Takes a Pandas series with entity name strings and converts them to pydeflate
    codes.

    Args:
        series: the Pandas series to convert.
        not_found: what to return when an entity name cannot be resolved.
            If None, the original value is passed through.
    """
    # Get the unique values for mapping to minimise resolver calls.
    s_unique = series.unique()

    mapping = _match_name_to_iso3(to_match=s_unique)
    return series.map(mapping).fillna(series if not_found is None else not_found)


def add_pydeflate_iso3(
    df: pd.DataFrame, column: str, *, fillna: Any = pd.NA
) -> pd.DataFrame:
    """Add a pydeflate_iso3 column resolved from the given entity-name column.

    Unresolved entity names become fillna (default pd.NA).

    Args:
        df (pd.DataFrame): The dataframe to add the column to.
        column (str): The column containing the entity name strings.
        fillna (Any): The value to use when the entity name is not resolved.

    Returns:
        pd.DataFrame: The dataframe with the added pydeflate_iso3 column.
    """
    df["pydeflate_iso3"] = convert_id(df[column].fillna(""), not_found=fillna)
    return df


def prefix_pydeflate_to_columns(
    df: pd.DataFrame, prefix: str = "pydeflate_"
) -> pd.DataFrame:
    """Add a prefix to all columns in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to add the prefix to.
        prefix (str): The prefix to add to the column names.

    Returns:
        pd.DataFrame: The DataFrame with the prefixed column names.
    """
    df.columns = [
        f"{prefix}{col}" if not col.startswith(prefix) else col for col in df.columns
    ]
    return df


def identify_base_year(df: pd.DataFrame, measure: str, year: str = "year") -> int:
    """Identify the base year for a given measure where the value is equal to 100.

    Args:
        df (pd.DataFrame): DataFrame containing the deflator
            data with 'year' and the given measure.
        measure (str): The column name for the measure to find the base year for.
        year (str): The column name for the year.

    Returns:
        int: The base year, or None if no base year is found.
    """
    # Find the year where the deflator measure is exactly 100 (or very close)
    base_year = df.loc[df[measure].round(2) == 100, year]

    # Return the year if found, otherwise return None
    return base_year.iloc[0] if not base_year.empty else None


def compute_exchange_deflator(
    df: pd.DataFrame,
    base_year_measure: str | None = None,
    exchange: str = "EXCHANGE",
    year: str = "year",
    grouper: list[str] | None = None,
) -> pd.DataFrame:
    """Compute the exchange rate deflator for each group of entities.

    This function calculates a deflator for the exchange
    rate by identifying a base year where the
    base_year_measure is 100, then normalizing exchange
    values to that base year.

    Args:
        df (pd.DataFrame): Input DataFrame containing
            columns 'year', and 'EXCHANGE'.
        base_year_measure (str): The column name for the
            measure to find the base year for.
        exchange (str): The column name for the exchange rate.
        year (str): The column name for the year.
        grouper (list): List of columns to group by before applying the deflator.

    Returns:
        pd.DataFrame: DataFrame with an additional column
            for the exchange rate deflator.
    """

    def _compute_deflator_for_group(
        group: pd.DataFrame,
        measure: str | None,
        exchange_col: str,
        year_col: str,
        deflator_col: str,
    ) -> pd.DataFrame:
        """Compute deflator for a single group and add it as a column."""
        # Identify base year
        if measure is not None:
            base_year = identify_base_year(group, measure=measure, year=year_col)
        else:
            valid_rows = group.dropna(subset=[exchange_col])
            base_year = valid_rows[year_col].max() if not valid_rows.empty else None

        # If no base year found, return group without deflator column
        if base_year is None or pd.isna(base_year):
            return group

        # Extract the exchange rate value for the base year
        base_value_rows = group.loc[group[year_col] == base_year, exchange_col]

        # If no valid base value, return group without deflator column
        if base_value_rows.empty or pd.isna(base_value_rows.iloc[0]):
            return group

        # Calculate and add deflator column
        base_value = base_value_rows.iloc[0]
        group = group.copy()
        group[deflator_col] = round(100 * group[exchange_col] / base_value, 6)

        return group

    if grouper is None:
        grouper = ["entity", "entity_code"]

    # Determine the exchange column name for the deflator
    exchange_name = (
        exchange.rsplit("_", 1)[0]
        if exchange.endswith("_to") or exchange.endswith("_from")
        else exchange
    )

    deflator_col = f"{exchange_name}_D"

    # Process each group and concatenate results
    # Avoids the FutureWarning from groupby().apply()
    # operating on grouping columns
    processed_groups = []
    for _name, group in df.groupby(grouper, sort=False):
        processed_group = _compute_deflator_for_group(
            group=group,
            measure=base_year_measure,
            exchange_col=exchange,
            year_col=year,
            deflator_col=deflator_col,
        )
        processed_groups.append(processed_group)

    # Concatenate all processed groups and restore original row order
    result = pd.concat(processed_groups, ignore_index=False)

    # Sort by index to restore original row order
    # (groupby may have changed the order when grouping rows together)
    result = result.sort_index()

    return result
