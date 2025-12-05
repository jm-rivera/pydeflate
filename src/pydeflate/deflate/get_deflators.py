from functools import wraps

import pandas as pd

from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import DAC, IMF, WorldBank


def _generate_get_deflator_docstring(source_name: str, price_kind: str) -> str:
    """Generate docstring for each get deflator function."""
    return (
        f"Get deflator data from {source_name} ({price_kind}) without requiring user data.\n\n"
        f"This function returns a DataFrame containing deflator values for the specified parameters.\n\n"
        "Args:\n"
        "    base_year (int): The base year for calculating deflation adjustments.\n"
        "    source_currency (str, optional): The source currency code. Defaults to 'USA'.\n"
        "    target_currency (str, optional): The target currency code. Defaults to 'USA'.\n"
        "    countries (list[str] | None, optional): List of country codes to include. If None, returns all. Defaults to None.\n"
        "    years (list[int] | range | None, optional): List or range of years to include. If None, returns all. Defaults to None.\n"
        "    use_source_codes (bool, optional): Use source-specific entity codes. Defaults to False.\n"
        "    to_current (bool, optional): Get deflators for constant-to-current conversion. Defaults to False.\n"
        "    include_components (bool, optional): Include price_deflator, exchange_deflator, and exchange_rate columns. Defaults to False.\n"
        "    update_deflators (bool, optional): Update the deflator data before retrieval. Defaults to False.\n\n"
        "Returns:\n"
        "    pd.DataFrame: DataFrame with columns:\n"
        "        - iso_code (or entity_code if use_source_codes=True): Country/entity identifier\n"
        "        - year: Year\n"
        "        - deflator: The combined deflator value\n"
        "        - price_deflator (if include_components=True): The price deflator component\n"
        "        - exchange_deflator (if include_components=True): The exchange rate deflator component\n"
        "        - exchange_rate (if include_components=True): The exchange rate\n"
    )


def _get_deflator(deflator_source_cls, price_kind):
    """Decorator to create get_deflator wrappers with specific deflator source and price kind."""

    def decorator(func):
        @wraps(func)
        def wrapper(
            *,
            base_year: int,
            source_currency: str = "USA",
            target_currency: str = "USA",
            countries: list[str] | None = None,
            years: list[int] | range | None = None,
            use_source_codes: bool = False,
            to_current: bool = False,
            include_components: bool = False,
            update_deflators: bool = False,
        ):
            # Validate input parameters
            if not isinstance(base_year, int):
                raise ValueError("The 'base_year' parameter must be an integer.")

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

            # Get the pydeflate data
            data = deflator.pydeflate_data.copy()

            # Determine the entity column based on use_source_codes
            entity_col = (
                "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3"
            )

            # Filter by countries if specified
            if countries is not None:
                data = data[data[entity_col].isin(countries)]

            # Filter by years if specified
            if years is not None:
                if isinstance(years, range):
                    years = list(years)
                data = data[data["pydeflate_year"].isin(years)]

            # Select columns to return
            columns_to_keep = [entity_col, "pydeflate_year", "pydeflate_deflator"]

            if include_components:
                # Add component columns
                price_col = f"pydeflate_{price_kind}"
                columns_to_keep.extend(
                    [price_col, "pydeflate_EXCHANGE_D", "pydeflate_EXCHANGE"]
                )

            # Keep only the specified columns
            result = data[columns_to_keep].copy()

            # Rename columns to user-friendly names
            rename_map = {
                entity_col: "entity_code" if use_source_codes else "iso_code",
                "pydeflate_year": "year",
                "pydeflate_deflator": "deflator",
            }

            if include_components:
                rename_map.update(
                    {
                        f"pydeflate_{price_kind}": "price_deflator",
                        "pydeflate_EXCHANGE_D": "exchange_deflator",
                        "pydeflate_EXCHANGE": "exchange_rate",
                    }
                )

            result = result.rename(columns=rename_map)

            # Reset index
            result = result.reset_index(drop=True)

            return result

        wrapper.__doc__ = _generate_get_deflator_docstring(
            deflator_source_cls.__name__, price_kind
        )
        return wrapper

    return decorator


@_get_deflator(DAC, "NGDP_D")
def get_oecd_dac_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_get_deflator(WorldBank, "NGDP_D")
def get_wb_gdp_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_get_deflator(WorldBank, "NGDP_DL")
def get_wb_gdp_linked_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_get_deflator(WorldBank, "CPI")
def get_wb_cpi_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_get_deflator(IMF, "NGDP_D")
def get_imf_gdp_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_get_deflator(IMF, "PCPI")
def get_imf_cpi_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...


@_get_deflator(IMF, "PCPIE")
def get_imf_cpi_e_deflators(
    *,
    base_year: int,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    to_current: bool = False,
    include_components: bool = False,
    update_deflators: bool = False,
) -> pd.DataFrame: ...
