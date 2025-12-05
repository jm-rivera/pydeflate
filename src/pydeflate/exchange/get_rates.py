from functools import wraps

import pandas as pd

from pydeflate.core.api import BaseExchange
from pydeflate.core.source import DAC, IMF, WorldBank, WorldBankPPP


def _generate_get_rates_docstring(source_name: str) -> str:
    """Generate docstring for each get exchange rates function."""
    return (
        f"Get exchange rate data from {source_name} without requiring user data.\n\n"
        f"This function returns a DataFrame containing exchange rates for the specified parameters.\n\n"
        "Args:\n"
        "    source_currency (str, optional): The source currency code. Defaults to 'USA'.\n"
        "    target_currency (str, optional): The target currency code. Defaults to 'USA'.\n"
        "    countries (list[str] | None, optional): List of country codes to include. If None, returns all. Defaults to None.\n"
        "    years (list[int] | range | None, optional): List or range of years to include. If None, returns all. Defaults to None.\n"
        "    use_source_codes (bool, optional): Use source-specific entity codes. Defaults to False.\n"
        "    update_rates (bool, optional): Update the exchange rate data before retrieval. Defaults to False.\n\n"
        "Returns:\n"
        "    pd.DataFrame: DataFrame with columns:\n"
        "        - iso_code (or entity_code if use_source_codes=True): Country/entity identifier\n"
        "        - year: Year\n"
        "        - exchange_rate: Exchange rate from source to target currency\n"
    )


def _get_exchange_rates(exchange_source_cls, **fixed_params):
    """Decorator to create get_exchange_rates wrappers with specific source."""

    def decorator(func):
        @wraps(func)
        def wrapper(
            *,
            source_currency: str = "USA",
            target_currency: str = "USA",
            countries: list[str] | None = None,
            years: list[int] | range | None = None,
            use_source_codes: bool = False,
            update_rates: bool = False,
        ):
            # Apply fixed parameters - no validation needed since these are internally set
            if "target_currency" in fixed_params:
                target_currency = fixed_params["target_currency"]

            # Initialize the exchange source
            if exchange_source_cls.__name__ == "WorldBankPPP":
                source = exchange_source_cls(
                    update=update_rates,
                    from_lcu=False if source_currency == "USA" else True,
                )
                source_currency = "LCU" if source_currency == "USA" else source_currency
            else:
                source = exchange_source_cls(update=update_rates)

            # Create an exchange object
            exchange = BaseExchange(
                exchange_source=source,
                source_currency=source_currency,
                target_currency=target_currency,
                use_source_codes=use_source_codes,
            )

            # Get the exchange rate data
            data = exchange.pydeflate_data.copy()

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

            # Select and rename columns
            result = data[[entity_col, "pydeflate_year", "pydeflate_EXCHANGE"]].copy()
            result = result.rename(
                columns={
                    entity_col: "entity_code" if use_source_codes else "iso_code",
                    "pydeflate_year": "year",
                    "pydeflate_EXCHANGE": "exchange_rate",
                }
            )

            # Reset index
            result = result.reset_index(drop=True)

            return result

        wrapper.__doc__ = _generate_get_rates_docstring(exchange_source_cls.__name__)
        return wrapper

    return decorator


@_get_exchange_rates(DAC)
def get_oecd_dac_exchange_rates(
    *,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    update_rates: bool = False,
) -> pd.DataFrame: ...


@_get_exchange_rates(WorldBank)
def get_wb_exchange_rates(
    *,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    update_rates: bool = False,
) -> pd.DataFrame: ...


def get_wb_ppp_rates(
    *,
    source_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    update_rates: bool = False,
) -> pd.DataFrame:
    """Get PPP exchange rate data from WorldBankPPP without requiring user data.

    This function returns a DataFrame containing PPP exchange rates for the specified parameters.

    Args:
        source_currency (str, optional): The source currency code. Defaults to 'USA'.
        countries (list[str] | None, optional): List of country codes to include. If None, returns all. Defaults to None.
        years (list[int] | range | None, optional): List or range of years to include. If None, returns all. Defaults to None.
        use_source_codes (bool, optional): Use source-specific entity codes. Defaults to False.
        update_rates (bool, optional): Update the exchange rate data before retrieval. Defaults to False.

    Returns:
        pd.DataFrame: DataFrame with columns:
            - iso_code (or entity_code if use_source_codes=True): Country/entity identifier
            - year: Year
            - exchange_rate: PPP exchange rate
    """
    # Initialize the exchange source
    source = WorldBankPPP(
        update=update_rates,
        from_lcu=False if source_currency == "USA" else True,
    )
    source_currency_internal = "LCU" if source_currency == "USA" else source_currency

    # Create an exchange object with PPP as target
    exchange = BaseExchange(
        exchange_source=source,
        source_currency=source_currency_internal,
        target_currency="PPP",
        use_source_codes=use_source_codes,
    )

    # Get the exchange rate data
    data = exchange.pydeflate_data.copy()

    # Determine the entity column based on use_source_codes
    entity_col = "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3"

    # Filter by countries if specified
    if countries is not None:
        data = data[data[entity_col].isin(countries)]

    # Filter by years if specified
    if years is not None:
        if isinstance(years, range):
            years = list(years)
        data = data[data["pydeflate_year"].isin(years)]

    # Select and rename columns
    result = data[[entity_col, "pydeflate_year", "pydeflate_EXCHANGE"]].copy()
    result = result.rename(
        columns={
            entity_col: "entity_code" if use_source_codes else "iso_code",
            "pydeflate_year": "year",
            "pydeflate_EXCHANGE": "exchange_rate",
        }
    )

    # Reset index
    result = result.reset_index(drop=True)

    return result


@_get_exchange_rates(IMF)
def get_imf_exchange_rates(
    *,
    source_currency: str = "USA",
    target_currency: str = "USA",
    countries: list[str] | None = None,
    years: list[int] | range | None = None,
    use_source_codes: bool = False,
    update_rates: bool = False,
) -> pd.DataFrame: ...
