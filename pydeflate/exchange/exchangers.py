from functools import wraps

import pandas as pd

from pydeflate.core.api import BaseExchange
from pydeflate.core.source import DAC, WorldBank, IMF


def _generate_docstring(source_name: str) -> str:
    """Generate docstring for each decorated exchange function."""
    return (
        f"Exchange a DataFrame using the {source_name} rates source.\n\n"
        f"This function applies exchange rates toa  DataFrame using the {source_name} rates.\n\n"
        "Args:\n"
        "    data (pd.DataFrame): The input DataFrame containing data to deflate.\n"
        "    source_currency (str, optional): The source currency code. Defaults to 'USA'.\n"
        "    target_currency (str, optional): The target currency code. Defaults to 'USA'.\n"
        "    id_column (str, optional): Column with entity identifiers. Defaults to 'iso_code'.\n"
        "    year_column (str, optional): Column with year information. Defaults to 'year'.\n"
        "    use_source_codes (bool, optional): Use source-specific entity codes. Defaults to False.\n"
        "    value_column (str, optional): Column with values to deflate. Defaults to 'value'.\n"
        "    target_value_column (str, optional): Column to store deflated values. Defaults to 'value'.\n"
        "    reversed_ (bool, optional): The reverse of an exchange conversion. Defaults to False.\n"
        "    year_format (str | None, optional): Format of the year in `year_column`. Defaults to None.\n"
        "    update_rates (bool, optional): Update the exchange rate data. Defaults to False.\n\n"
        "Returns:\n"
        "    pd.DataFrame: DataFrame with converted values in the `target_value_column`.\n"
    )


def _exchange(exchange_source_cls):
    """Decorator to create exchange wrappers with specific source"""

    def decorator(func):
        @wraps(func)
        def wrapper(
            data: pd.DataFrame,
            *,
            source_currency: str = "USA",
            target_currency: str = "USA",
            id_column: str = "iso_code",
            year_column: str = "year",
            use_source_codes: bool = False,
            value_column: str = "value",
            target_value_column: str = "value",
            reversed_: bool = False,
            year_format: str | None = None,
            update_rates: bool = False,
        ):
            # Validate input parameters
            if not isinstance(data, pd.DataFrame):
                raise ValueError("The 'data' parameter must be a pandas DataFrame.")

            if id_column not in data.columns:
                raise ValueError(
                    f"The id_column '{id_column}' is not in the DataFrame."
                )
            if year_column not in data.columns:
                raise ValueError(
                    f"The year_column '{year_column}' is not in the DataFrame."
                )
            if value_column not in data.columns:
                raise ValueError(
                    f"The value_column '{value_column}' is not in the DataFrame."
                )

            # Copy the data to avoid modifying the original
            to_exchange = data.copy()

            # Initialize the deflator source
            source = exchange_source_cls(update=update_rates)

            # Create a deflator object
            exchange = BaseExchange(
                exchange_source=source,
                source_currency=source_currency,
                target_currency=target_currency,
                use_source_codes=use_source_codes,
            )

            # Deflate the data
            return exchange.exchange(
                data=to_exchange,
                entity_column=id_column,
                year_column=year_column,
                value_column=value_column,
                target_value_column=target_value_column,
                year_format=year_format,
                reversed_=reversed_,
            )

        # Add the deflator source and price kind to the function
        wrapper.__doc__ = _generate_docstring(exchange_source_cls.__name__)
        return wrapper

    return decorator


@_exchange(DAC)
def oecd_dac_exchange(
    data: pd.DataFrame,
    *,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    reversed_: bool = False,
    year_format: str | None = None,
    update_rates: bool = False,
) -> pd.DataFrame: ...


@_exchange(WorldBank)
def wb_exchange(
    data: pd.DataFrame,
    *,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    reversed_: bool = False,
    year_format: str | None = None,
    update_rates: bool = False,
) -> pd.DataFrame: ...


@_exchange(IMF)
def imf_exchange(
    data: pd.DataFrame,
    *,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    reversed_: bool = False,
    year_format: str | None = None,
    update_rates: bool = False,
) -> pd.DataFrame: ...
