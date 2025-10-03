from functools import wraps

import pandas as pd

from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import DAC, WorldBank, IMF


def _generate_docstring(source_name: str, price_kind: str) -> str:
    """Generate docstring for each decorated deflation function."""
    return (
        f"Deflate a DataFrame using the {source_name} deflator source ({price_kind}).\n\n"
        f"This function applies deflation adjustments to a DataFrame using the {source_name} {price_kind} deflator.\n\n"
        "Args:\n"
        "    data (pd.DataFrame): The input DataFrame containing data to deflate.\n"
        "    base_year (int): The base year for calculating deflation adjustments.\n"
        "    source_currency (str, optional): The source currency code. Defaults to 'USA'.\n"
        "    target_currency (str, optional): The target currency code. Defaults to 'USA'.\n"
        "    id_column (str, optional): Column with entity identifiers. Defaults to 'iso_code'.\n"
        "    year_column (str, optional): Column with year information. Defaults to 'year'.\n"
        "    use_source_codes (bool, optional): Use source-specific entity codes. Defaults to False.\n"
        "    value_column (str, optional): Column with values to deflate. Defaults to 'value'.\n"
        "    target_value_column (str, optional): Column to store deflated values. Defaults to 'value'.\n"
        "    to_current (bool, optional): Adjust values to current-year values if True. Defaults to False.\n"
        "    year_format (str | None, optional): Format of the year in `year_column`. Defaults to None.\n"
        "    update_deflators (bool, optional): Update the deflator data before deflation. Defaults to False.\n\n"
        "Returns:\n"
        "    pd.DataFrame: DataFrame with deflated values in the `target_value_column`.\n"
    )


def _deflator(deflator_source_cls, price_kind):
    """Decorator to create deflate wrappers with specific deflator source and price kind."""

    def decorator(func):
        @wraps(func)
        def wrapper(
            data: pd.DataFrame,
            *,
            base_year: int,
            source_currency: str = "USA",
            target_currency: str = "USA",
            id_column: str = "iso_code",
            year_column: str = "year",
            use_source_codes: bool = False,
            value_column: str = "value",
            target_value_column: str = "value",
            to_current: bool = False,
            year_format: str | None = None,
            update_deflators: bool = False,
        ):
            # Validate input parameters
            if not isinstance(data, pd.DataFrame):
                raise ValueError("The 'data' parameter must be a pandas DataFrame.")
            if not isinstance(base_year, int):
                raise ValueError("The 'base_year' parameter must be an integer.")
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
            to_deflate = data.copy()

            # Initialize the deflator source
            source = deflator_source_cls(update=update_deflators)

            # Create a deflator object
            deflator = BaseDeflate(
                base_year=base_year,
                deflator_source=source,
                exchange_source=source,
                source_currency=source_currency,
                target_currency=target_currency,
                price_kind=price_kind,
                use_source_codes=use_source_codes,
                to_current=to_current,
            )

            # Deflate the data
            return deflator.deflate(
                data=to_deflate,
                entity_column=id_column,
                year_column=year_column,
                value_column=value_column,
                target_value_column=target_value_column,
                year_format=year_format,
            )

        # Add the deflator source and price kind to the function
        wrapper.__doc__ = _generate_docstring(deflator_source_cls.__name__, price_kind)
        return wrapper

    return decorator


@_deflator(DAC, "NGDP_D")
def oecd_dac_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_deflator(WorldBank, "NGDP_D")
def wb_gdp_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
): ...


@_deflator(WorldBank, "NGDP_D")
def wb_gdp_linked_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
): ...


@_deflator(WorldBank, "CPI")
def wb_cpi_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
): ...


@_deflator(IMF, "NGDP_D")
def imf_gdp_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
): ...


@_deflator(IMF, "PCPI")
def imf_cpi_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
): ...


@_deflator(IMF, "PCPIE")
def imf_cpi_e_deflate(
    data: pd.DataFrame,
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    id_column: str = "iso_code",
    year_column: str = "year",
    use_source_codes: bool = False,
    value_column: str = "value",
    target_value_column: str = "value",
    to_current: bool = False,
    year_format: str | None = None,
    update_deflators: bool = False,
): ...
