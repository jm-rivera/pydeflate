import pandas as pd

from pydeflate.core.deflator import ExchangeDeflator, PriceDeflator
from pydeflate.core.exchange import Exchange
from pydeflate.core.source import Source
from pydeflate.sources.common import AvailableDeflators
from pydeflate.utils import (
    create_pydeflate_year,
    merge_user_and_pydeflate_data,
    get_unmatched_pydeflate_data,
    get_matched_pydeflate_data,
    flag_missing_pydeflate_data,
)


def resolve_common_currencies(currency: str, source: str) -> str:
    mapping = {
        "USD": "USA",
        "EUR": "EUR",
        "GBP": "GBR",
        "JPY": "JPN",
        "CAD": "CAN",
    }

    if source == "DAC":
        mapping["EUR"] = "EUI"

    return mapping.get(currency, currency)


def _base_operation(
    base_obj,
    data: pd.DataFrame,
    entity_column: str,
    year_column: str,
    value_column: str,
    target_value_column: str | None = None,
    year_format: str | None = None,
    exchange: bool = False,
    reversed_: bool = False,
):
    """Perform deflation or exchange rate adjustment on input data using pydeflate data.

    Args:
        base_obj (BaseExchange | BaseDeflate): The base object containing pydeflate data.
        data (pd.DataFrame): Data to be adjusted.
        entity_column (str): Column with entity or country identifiers.
        year_column (str): Column with year information.
        value_column (str): Column with values to be adjusted.
        target_value_column (str | None, optional): Column to store adjusted values. Defaults to `value_column`.
        year_format (str, optional): Format of the year. Defaults to "%Y".
        exchange (bool, optional): Whether to perform an exchange rate adjustment (True)
        or deflation (False).
        reversed_ (bool, optional): If True, perform the operation in reverse.

    Returns:
        pd.DataFrame: DataFrame with adjusted values and original columns preserved.
    """
    # Make a copy of the input data to avoid modifying the original data
    data = data.copy(deep=True)

    target_value_column = target_value_column or value_column

    # Keep track of original columns to return data in the same order.
    cols = (
        [*data.columns, target_value_column]
        if target_value_column not in data.columns
        else data.columns
    )

    # Merge pydeflate data to the input data
    base_obj._merge_pydeflate_data(
        data=data,
        entity_column=entity_column,
        year_column=year_column,
        year_format=year_format,
    )

    # Flag missing data
    flag_missing_pydeflate_data(
        base_obj._unmatched_data, entity_column=entity_column, year_column=year_column
    )
    x = base_obj._merged_data[value_column]
    y = base_obj._merged_data[
        "pydeflate_EXCHANGE" if exchange else "pydeflate_deflator"
    ]

    # Apply the correct operation based on `exchange` and `reversed`
    if (exchange and not reversed_) or (not exchange and reversed_):
        base_obj._merged_data[target_value_column] = (x * y).round(6)
    else:
        base_obj._merged_data[target_value_column] = (x / y).round(6)

    return base_obj._merged_data[cols]


class BaseExchange:
    """Performs currency exchange rate conversions within data, using pydeflate.

    Provides methods to merge pydeflate exchange rate data with user data and apply
    exchange rate adjustments, allowing for straightforward currency conversions
    within a dataset.
    """

    def __init__(
        self,
        exchange_source: Source,
        source_currency: str,
        target_currency: str,
        use_source_codes: bool = False,
    ):
        """Initialize a BaseExchange instance with exchange rate data and identifiers.

        Args:
            exchange_source (Source): Data source for exchange rates.
            source_currency (str): Original currency for conversion.
            target_currency (str): Target currency for conversion.
            use_source_codes (bool, optional): Use source-specific entity codes.
             Defaults to False.
        """

        # Try to accept common currencies by their country codes
        source_currency = resolve_common_currencies(
            source_currency, exchange_source.name
        )

        target_currency = resolve_common_currencies(
            target_currency, exchange_source.name
        )

        self.exchange_rates = Exchange(
            source=exchange_source,
            source_currency=source_currency,
            target_currency=target_currency,
        )

        self._idx = [
            "pydeflate_year",
            "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3",
        ]

        self._load_pydeflate_data()

    def _load_pydeflate_data(self) -> None:
        """Load and prepare pydeflate exchange rate data."""
        self.pydeflate_data = (
            self.exchange_rates.exchange_data.set_index(self._idx)
            .dropna(how="any")
            .reset_index()
        )

    def _merge_pydeflate_data(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        year_format: str | None = None,
    ) -> None:
        """Merge pydeflate exchange rate data into input data by year and entity.

        Args:
            data (pd.DataFrame): Input DataFrame to merge with pydeflate data.
            entity_column (str): Column name for entity or country codes.
            year_column (str): Column name for year information.
            year_format (str, optional): Year format. Defaults to '%Y'.
        """

        # Convert the year to an integer
        data = create_pydeflate_year(
            data=data, year_column=year_column, year_format=year_format
        )

        # Merge data to the input data based on year and entity
        merged_data = merge_user_and_pydeflate_data(
            data=data,
            pydeflate_data=self.pydeflate_data,
            entity_column=entity_column,
            ix=self._idx,
            source_codes=self._idx[-1] == "pydeflate_entity_code",
            dac=self.exchange_rates.source.name == "DAC",
        )

        # store unmatched data
        self._unmatched_data = get_unmatched_pydeflate_data(merged_data=merged_data)

        # store matched data
        self._merged_data = get_matched_pydeflate_data(merged_data=merged_data)

    def exchange(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        value_column: str,
        target_value_column: str | None = None,
        year_format: str | None = None,
        reversed_: bool = False,
    ):
        """Apply exchange rate conversion to input data.

        Args:
            data (pd.DataFrame): Data to apply exchange rate adjustment.
            entity_column (str): Column with entity identifiers.
            year_column (str): Column with year information.
            value_column (str): Column with values to adjust.
            target_value_column (str | None, optional): Column for adjusted values. Defaults to `value_column`.
            year_format (str, optional): Format of the year. Defaults to "%Y".
            reversed_ (bool, optional): If True, perform the operation in reverse. defaults to False.

        Returns:
            pd.DataFrame: DataFrame with exchange rate-adjusted values.
        """
        return _base_operation(
            base_obj=self,
            exchange=True,
            data=data,
            entity_column=entity_column,
            year_column=year_column,
            value_column=value_column,
            target_value_column=target_value_column,
            year_format=year_format,
            reversed_=reversed_,
        )


class BaseDeflate:
    """Deflating monetary values over time with exchange rates and price indices.

    Combines price deflators, exchange rate deflators, and pydeflate data to allow
    for adjustments of monetary values across different time periods, enabling accurate
    economic comparisons over time.
    """

    def __init__(
        self,
        deflator_source: Source,
        exchange_source: Source,
        base_year: int,
        price_kind: AvailableDeflators,
        source_currency: str,
        target_currency: str,
        use_source_codes: bool = False,
        to_current: bool = False,
    ):
        """Initialize a BaseDeflate instance with deflator and exchange rate sources.

        Args:
            deflator_source (Source): Data source for price deflators.
            exchange_source (Source): Data source for exchange rates.
            base_year (int): Reference year for base value adjustments.
            price_kind (AvailableDeflators): Type of deflator (e.g., CPI).
            source_currency (str): Currency of the input data.
            target_currency (str): Currency for conversion.
            use_source_codes (bool, optional): Use source-specific entity codes. Defaults to False.
            to_current (bool, optional): If True, adjust to current year values. Defaults to False.
        """

        # Try to accept common currencies by their country codes
        source_currency = resolve_common_currencies(
            source_currency, deflator_source.name
        )

        target_currency = resolve_common_currencies(
            target_currency, deflator_source.name
        )
        self.exchange_rates = Exchange(
            source=exchange_source,
            source_currency=source_currency,
            target_currency=target_currency,
        )

        self.exchange_deflator = ExchangeDeflator(
            source=self.exchange_rates, base_year=base_year
        )

        self.price_deflator = PriceDeflator(
            source=deflator_source, kind=price_kind, base_year=base_year
        )

        self._idx = [
            "pydeflate_year",
            "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3",
        ]

        self.use_source_codes = use_source_codes
        self.to_current = to_current

        self.__post_init__()

    def __post_init__(self):
        """Post-initialization process to merge deflator, exchange, and pydeflate data."""

        # Merge deflator and exchange rate data
        data = self._merge_components(
            df=self.price_deflator.deflator_data,
            other=self.exchange_deflator.deflator_data,
        ).pipe(self._merge_components, other=self.exchange_rates.exchange_data)

        # drop where necessary data is missing
        data = data.set_index(self._idx).dropna(how="any").reset_index()

        # Calculate price-exchange deflator
        data["pydeflate_deflator"] = self._calculate_deflator_value(
            data[f"pydeflate_{self.price_deflator.price_kind}"],
            data["pydeflate_EXCHANGE_D"],
            data[f"pydeflate_EXCHANGE"],
        )

        self.pydeflate_data = data

    def _calculate_deflator_value(
        self, price_def: pd.Series, exchange_def: pd.Series, exchange_rate: pd.Series
    ):
        """Compute the combined deflator value using price deflator, exchange deflator, and rates.

        Args:
            price_def (pd.Series): Series of price deflator values.
            exchange_def (pd.Series): Series of exchange deflator values.
            exchange_rate (pd.Series): Series of exchange rates.

        Returns:
            pd.Series: Series with combined deflator values.
        """
        return (
            (exchange_def * exchange_rate) / price_def
            if self.to_current
            else price_def / (exchange_def * exchange_rate)
        )

    def _merge_components(self, df: pd.DataFrame, other: pd.DataFrame):
        """Combine data components, merging deflator and exchange rate information.

        Args:
            df (pd.DataFrame): Main DataFrame for merging.
            other (pd.DataFrame): Additional data to merge into `df`.

        Returns:
            pd.DataFrame: Merged DataFrame without duplicate columns.
        """
        merged = df.merge(other, how="outer", on=self._idx, suffixes=("", "_ex"))
        return merged.drop(columns=merged.filter(regex=f"_ex$").columns, axis=1)

    def _merge_pydeflate_data(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        year_format: str | None = None,
    ) -> None:
        """Merge pydeflate deflator data into the input data by year and entity.

        Args:
            data (pd.DataFrame): Input DataFrame to merge with pydeflate data.
            entity_column (str): Column for entity or country identifiers.
            year_column (str): Column for year information.
            year_format (str, optional): Format of the year. Defaults to '%Y'.
        """

        # Convert the year to an integer
        data = create_pydeflate_year(
            data=data, year_column=year_column, year_format=year_format
        )

        # Merge data to the input data based on year and entity
        merged_data = merge_user_and_pydeflate_data(
            data=data,
            pydeflate_data=self.pydeflate_data,
            entity_column=entity_column,
            ix=self._idx,
            source_codes=self.use_source_codes,
            dac=self.exchange_deflator.source.name == "DAC"
            or self.price_deflator.source.name == "DAC",
        )

        # store unmatched data
        self._unmatched_data = get_unmatched_pydeflate_data(merged_data=merged_data)

        # store matched data
        self._merged_data = get_matched_pydeflate_data(merged_data=merged_data)

    def deflate(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        value_column: str,
        target_value_column: str | None = None,
        year_format: str | None = None,
    ):
        """Apply deflation adjustment to input data using pydeflate deflator rates.

        Args:
            data (pd.DataFrame): Data for deflation adjustment.
            entity_column (str): Column with entity identifiers.
            year_column (str): Column with year information.
            value_column (str): Column with values to deflate.
            target_value_column (str | None, optional): Column to store deflated values. Defaults to `value_column`.
            year_format (str, optional): Format of the year. Defaults to "%Y".

        Returns:
            pd.DataFrame: DataFrame with deflated values.
        """
        return _base_operation(
            base_obj=self,
            data=data,
            entity_column=entity_column,
            year_column=year_column,
            value_column=value_column,
            target_value_column=target_value_column,
            year_format=year_format,
        )
