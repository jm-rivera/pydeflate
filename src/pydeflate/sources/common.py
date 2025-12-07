from __future__ import annotations

from typing import Any, Literal

import pandas as pd
from hdx.location.country import Country

from pydeflate.pydeflate_config import logger

AvailableDeflators = Literal["NGDP_D", "NGDP_DL", "CPI", "PCPI", "PCPIE"]


def enforce_pyarrow_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure that a DataFrame uses pyarrow-backed dtypes."""

    return df.convert_dtypes(dtype_backend="pyarrow")


def _match_regex_to_iso3(
    to_match: list[str], additional_mapping: dict | None
) -> dict[str, str]:
    """Match a list of regex strings to ISO3 country codes.

    Args:
        to_match (list): A list of regex strings to match.

    Returns:
        dict: A dictionary with the regex strings as keys and the ISO3 codes as values.
    """
    if additional_mapping is None:
        additional_mapping = {}

    country = Country()
    matches: dict[str, str | None] = {}

    for match in to_match:
        try:
            match_ = country.get_iso3_country_code_fuzzy(match)[0]
        except Exception:  # pragma: no cover - defensive logging
            match_ = None
        matches[match] = match_
        if match_ is None and match not in additional_mapping:
            logger.debug("No ISO3 match found for %s", match)

    return matches | additional_mapping


def convert_id(
    series: pd.Series,
    from_type: str = "regex",
    to_type: str = "ISO3",
    not_found: Any = None,
    *,
    additional_mapping: dict | None = None,
) -> pd.Series:
    """Takes a Pandas' series with country IDs and converts them into the desired type.

    Args:
        series: the Pandas series to convert
        from_type: the classification type according to which the series is encoded.
            For example: ISO3, ISO2, regex, DACCode.
        to_type: the target classification type. Same options as from_type
        not_found: what to do if the value is not found. Can pass a string or None.
            If None, the original value is passed through.
        additional_mapping: Optionally, a dictionary with additional mappings can be used.
            The keys are the values to be converted and the values are the converted values.
            The keys follow the same datatype as the original values. The values must follow
            the same datatype as the target type.
    """

    if from_type == to_type:
        return series

    mapping_functions = {"regex": _match_regex_to_iso3}

    # Get the unique values for mapping. This is done in order to significantly improve
    # the performance of country_converter with very long datasets.
    s_unique = series.unique()

    # Create a correspondence dictionary
    mapping = mapping_functions[from_type](
        to_match=s_unique, additional_mapping=additional_mapping
    )
    return series.map(mapping).fillna(series if not_found is None else not_found)


def add_pydeflate_iso3(
    df: pd.DataFrame, column: str, from_type: str = "regex", fillna: Any = pd.NA
) -> pd.DataFrame:
    """Add a column with ISO3 country codes to a dataframe.

    Args:
        df (pd.DataFrame): The dataframe to add the column to.
        column (str): The column containing the country codes.
        from_type (str): The classification type of the country codes.
        fillna (Any): The value to use when the country code is not found.

    Returns:
        pd.DataFrame: The dataframe with the added ISO3 column.
    """
    # Convert the country codes to ISO3
    df["pydeflate_iso3"] = convert_id(
        df[column].fillna(""),
        from_type=from_type,
        to_type="ISO3",
        not_found=fillna,
        additional_mapping={
            "World": "WLD",
            "European Union": "EUR",
            "European Union (EU)": "EUR",
            "Euro area": "EUR",
            "Euro Area (EA)": "EUR",
            "EU Institutions": "EUI",
            "DAC countries": "DAC",
            "DAC Countries, Total": "DAC",
            "Total DAC": "DAC",
            "Kosovo": "XXK",
            "Kosovo, Republic of": "XXK",
            "G7": "G7C",
            "Sub-Sahara Africa": "SSA",
        },
    )
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
        df (pd.DataFrame): DataFrame containing the deflator data with 'year' and the given measure.
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

    This function calculates a deflator for the exchange rate by identifying a base year
    where the base_year_measure is 100, then normalizing exchange values to that base year.

    Args:
        df (pd.DataFrame): Input DataFrame containing columns 'year', and 'EXCHANGE'.
        base_year_measure (str): The column name for the measure to find the base year for.
        exchange (str): The column name for the exchange rate.
        year (str): The column name for the year.
        grouper (list): List of columns to group by before applying the deflator.

    Returns:
        pd.DataFrame: DataFrame with an additional column for the exchange rate deflator.
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
    if exchange.endswith("_to") or exchange.endswith("_from"):
        exchange_name = exchange.rsplit("_", 1)[0]
    else:
        exchange_name = exchange

    deflator_col = f"{exchange_name}_D"

    # Process each group and concatenate results
    # This approach avoids the FutureWarning from groupby().apply() operating on grouping columns
    processed_groups = []
    for name, group in df.groupby(grouper, sort=False):
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
