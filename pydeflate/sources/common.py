from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from hdx.location.country import Country

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger

AvailableDeflators = Literal["NGDP_D", "NGDP_DL", "CPI", "PCPI", "PCPIE"]


def check_file_age(file: Path) -> int:
    """Check the age of a WEO file in days.

    Args:
        file (Path): The WEO parquet file to check.

    Returns:
        int: The number of days since the file was created.
    """
    current_date = datetime.today()
    # Extract date from the filename (format: weo_YYYY-MM-DD.parquet)
    file_date = datetime.strptime(file.stem.split("_")[-1], "%Y-%m-%d")

    # Return the difference in days between today and the file's date
    return (current_date - file_date).days


def enforce_pyarrow_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures that a DataFrame uses pyarrow dtypes."""
    return df.convert_dtypes(dtype_backend="pyarrow")


def today() -> str:
    from datetime import datetime

    return datetime.today().strftime("%Y-%m-%d")


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

    # Create a Country object
    country = Country()

    # Match the regex strings to ISO3 country codes
    matches = {}

    for match in to_match:
        try:
            match_ = country.get_iso3_country_code_fuzzy(match)[0]
        except:
            match_ = None
        matches[match] = match_
        if match_ is None and match not in additional_mapping:
            logger.debug(f"No ISO3 match found for {match}")

    return matches | additional_mapping


def convert_id(
    series: pd.Series,
    from_type: str = "regex",
    to_type: str = "ISO3",
    not_found: Any = None,
    *,
    additional_mapping: dict = None,
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

    # if from and to are the same, return without changing anything
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
            "EU Institutions": "EUI",
            "DAC countries": "DAC",
            "Kosovo": "XXK",
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
    grouper: list[str] = None,
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

    def _add_deflator(
        group: pd.DataFrame,
        measure: str | None = "NGDPD_D",
        exchange: str = "EXCHANGE",
        year: str = "year",
    ) -> pd.DataFrame:

        # if needed, clean exchange name
        if exchange.endswith("_to") or exchange.endswith("_from"):
            exchange_name = exchange.rsplit("_", 1)[0]
        else:
            exchange_name = exchange

        # Identify the base year for the deflator
        if measure is not None:
            base_year = identify_base_year(group, measure=measure, year=year)
        else:
            base_year = group.dropna(subset=exchange)[year].max()

        # If no base year is found, return the group unchanged
        if base_year is None or pd.isna(base_year):
            return group

        # Extract the exchange rate value for the base year
        base_value = group.loc[group[year] == base_year, exchange].values

        # If base value is found and valid, calculate the deflator
        if base_value.size > 0 and pd.notna(base_value[0]):
            group[f"{exchange_name}_D"] = round(
                100 * group[exchange] / base_value[0], 6
            )

        return group

    if grouper is None:
        grouper = ["entity", "entity_code"]

    # Apply the deflator computation for each group of 'entity' and 'entity_code'
    return df.groupby(grouper, group_keys=False).apply(
        _add_deflator, measure=base_year_measure, exchange=exchange, year=year
    )


def read_data(
    file_finder_func: callable,
    download_func: callable,
    data_name: str,
    update: bool = False,
) -> pd.DataFrame:
    """Generic function to read data from parquet files or download fresh data.

    Args:
        file_finder_func (function): Function to find existing data files in the path.
        download_func (function): Function to download fresh data if no files are
        found or an update is needed.
        data_name (str): Name of the dataset for logging purposes (e.g., "WEO", "DAC").
        update (bool): If True, forces downloading of new data even if files exist.

    Returns:
        pd.DataFrame: The latest available data.
    """
    # Find existing files using the provided file finder function
    files = file_finder_func(PYDEFLATE_PATHS.data)

    # If no files are found or update is requested, download new data
    if len(files) == 0 or update:
        download_func()
        files = file_finder_func(PYDEFLATE_PATHS.data)

    # If files are found, sort them by age and load the most recent one
    if len(files) > 0:
        files = sorted(files, key=check_file_age)
        latest_file = files[0]

        # Check if the latest file is older than 120 days and log a warning
        if check_file_age(latest_file) > 120:
            logger.warn(
                f"The latest {data_name} data is more than 120 days old.\n"
                f"Consider updating by setting update=True in the function call."
            )

        # Read and return the latest parquet file as a DataFrame
        logger.info(f"Reading {data_name} data from {latest_file}")
        return pd.read_parquet(latest_file)
