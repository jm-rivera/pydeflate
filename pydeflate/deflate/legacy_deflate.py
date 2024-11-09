import warnings

import pandas as pd
from pandas.util._decorators import deprecate_kwarg


@deprecate_kwarg(old_arg_name="method", new_arg_name="deflator_method")
@deprecate_kwarg(old_arg_name="source", new_arg_name="deflator_source")
@deprecate_kwarg(old_arg_name="iso_column", new_arg_name="id_column")
@deprecate_kwarg(old_arg_name="source_col", new_arg_name="source_column")
@deprecate_kwarg(old_arg_name="target_col", new_arg_name="target_column")
def deflate(
    df: pd.DataFrame,
    base_year: int,
    deflator_source: str,
    deflator_method: str,
    exchange_source: str,
    exchange_method: str,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    id_type: str = "ISO3",
    date_column: str = "date",
    source_column: str = "value",
    target_column: str = "value",
    to_current: bool = False,
) -> pd.DataFrame:
    """DEPRECATED: Use pydeflate's updated API for deflation adjustments.

    This legacy function is provided for backwards compatibility only.
    Please refer to the latest documentation for using pydeflate's updated API.

    Args:
        df (pd.DataFrame): DataFrame with flow data to be deflated.
        base_year (int): Target year for base value adjustments.
        deflator_source (str): Source of deflator data, e.g., 'oecd_dac', 'wb', 'imf'.
        deflator_method (str): Method for deflator calculation, e.g., 'gdp', 'cpi'.
        exchange_source (str): Source for exchange rates.
        exchange_method (str): Method for exchange rate calculation.
        source_currency (str): ISO3 code for the source currency.
        target_currency (str): ISO3 code for the target currency.
        id_column (str): Column for entity identifiers, e.g., 'iso_code'.
        id_type (str): Type of ID classification; default is 'ISO3'.
        date_column (str): Column for date information.
        source_column (str): Column with original monetary values.
        target_column (str): Column to store deflated values.
        to_current (bool): If True, convert to current prices.

    Returns:
        pd.DataFrame: DataFrame with deflated values.
    """
    warnings.warn(
        "The `deflate` function is deprecated and will be removed in future versions. "
        "Please check the latest documentation for updated methods.",
        DeprecationWarning,
    )
