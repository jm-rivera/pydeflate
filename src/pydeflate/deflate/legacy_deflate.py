import functools
import warnings
from collections.abc import Callable

import pandas as pd

from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import DAC, IMF, WorldBank

_RENAMED_KWARGS: dict[str, str] = {
    "method": "deflator_method",
    "source": "deflator_source",
    "iso_column": "id_column",
    "source_col": "source_column",
    "target_col": "target_column",
}


def _remap_deprecated_kwargs(func: Callable) -> Callable:
    """Emit deprecation warnings for renamed keyword arguments and forward them."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for old_name, new_name in _RENAMED_KWARGS.items():
            if old_name in kwargs:
                if new_name in kwargs:
                    raise TypeError(
                        f"Cannot specify both '{old_name}' and '{new_name}'."
                    )
                warnings.warn(
                    f"The '{old_name}' keyword argument is deprecated. "
                    f"Use '{new_name}' instead.",
                    FutureWarning,
                    stacklevel=2,
                )
                kwargs[new_name] = kwargs.pop(old_name)
        return func(*args, **kwargs)

    return wrapper


@_remap_deprecated_kwargs
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
        stacklevel=2,
    )

    if id_type != "ISO3":
        raise ValueError(
            "Only ISO3 ID classification is supported in this version.\n"
            "You can use bblocks to convert to ISO3."
        )

    price_kind = {
        "oecd_dac": "NGDP_D",
        "dac_deflator": "NGDP_D",
        "gdp": "NGDP_D",
        "cpi": "CPI",
    }

    # Mapping of string identifiers to classes and price kinds
    deflator_source_map = {
        "oecd_dac": DAC,
        "dac": DAC,
        "wb": WorldBank,
        "world_bank": WorldBank,
        "imf": IMF,
    }

    deflator_source = deflator_source_map[deflator_source.lower()]()
    exchange_source = deflator_source_map[exchange_source.lower()]()
    deflator_method = price_kind.get(deflator_method.lower(), deflator_method).upper()

    # Copy the data to avoid modifying the original
    to_deflate = df.copy()

    # Create a deflator object
    deflator = BaseDeflate(
        base_year=base_year,
        deflator_source=deflator_source,
        exchange_source=exchange_source,
        source_currency=source_currency,
        target_currency=target_currency,
        price_kind=deflator_method,
        to_current=to_current,
    )

    # Deflate the data
    return deflator.deflate(
        data=to_deflate,
        entity_column=id_column,
        year_column=date_column,
        value_column=source_column,
        target_value_column=target_column,
        year_format=None,
    )
