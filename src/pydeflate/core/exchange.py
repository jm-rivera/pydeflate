from dataclasses import dataclass, field

import pandas as pd

from pydeflate.core.source import Source
from pydeflate.sources.common import compute_exchange_deflator


@dataclass
class Exchange:
    """A class to manage and process exchange rate data for currency conversions.

    This class holds exchange rate data and provides methods to apply exchange rates
    for conversions between source and target currencies.

    Attributes:
        source (Source): An instance of the Source class to fetch exchange rate data.
        source_currency (str): The source currency code (default is 'LCU' - Local Currency Unit).
        target_currency (str): The target currency code (default is 'USA' - US Dollar).
        exchange_data (pd.DataFrame): DataFrame holding the exchange rate data.
    """

    source: Source
    source_currency: str = "LCU"
    target_currency: str = "USA"
    exchange_data: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        """Initialize the Exchange object and process the exchange rate data."""
        # Load and filter the relevant columns from the exchange rate data
        self.exchange_data = self.source.lcu_usd_exchange()

        if self.source_currency == self.target_currency:
            self.exchange_data = self.exchange_rate("LCU", self.target_currency)
            self.exchange_data["pydeflate_EXCHANGE"] = 1
        else:
            self.exchange_data = self.exchange_rate(
                self.source_currency, self.target_currency
            )

    def _get_exchange_rate(self, currency):
        """Helper function to fetch exchange rates for a given currency."""
        exchange_rate = self.exchange_data.loc[
            self.exchange_data["pydeflate_iso3"] == currency
        ]
        return exchange_rate

    def _convert_exchange(self, to_: str) -> pd.DataFrame:
        """Converts exchange rates based on the target currency.

        This method retrieves exchange rates for a given target currency, merges the
        target exchange rates with the base exchange rates, and computes the final
        exchange rate by dividing the base exchange rate by the target exchange rate.

        Args:
            to_ (str): The target currency code.

        Returns:
            pd.DataFrame: A DataFrame with the adjusted exchange rates for the target currency.

        Raises:
            ValueError: If no exchange rate data is available for the target currency.
        """

        if to_ == "LCU":
            return self.exchange_data.copy().assign(pydeflate_EXCHANGE=1)

        usd_rate = self.exchange_data.copy()
        target_exchange = self._get_exchange_rate(to_)

        if target_exchange.empty:
            raise ValueError(f"No currency exchange data for {to_=}")

        merged = pd.merge(
            usd_rate,
            target_exchange,
            how="left",
            on=["pydeflate_year"],
            suffixes=("", "_to"),
        ).assign(
            pydeflate_EXCHANGE=lambda d: d.pydeflate_EXCHANGE / d.pydeflate_EXCHANGE_to,
        )

        return merged.drop(columns=merged.filter(regex="_to$").columns, axis=1)

    def exchange_rate(self, from_currency: str, to_currency: str):
        """Calculates the exchange rates between the source and target currencies.

        Args:
            from_currency (str): The source currency code.
            to_currency (str): The target currency code.

        Returns:
            None
        """
        # Get exchange data based on the source currency.
        source = self._convert_exchange(to_=from_currency)

        # Get exchange data based on the target currency.
        target = self._convert_exchange(to_=to_currency)

        # Merge the source and target exchange data and compute the final exchange rate.
        merged = pd.merge(
            source,
            target,
            how="left",
            on=["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"],
            suffixes=("", "_to"),
        ).assign(
            pydeflate_EXCHANGE=lambda d: d.pydeflate_EXCHANGE / d.pydeflate_EXCHANGE_to
        )

        # Compute the exchange rate deflator
        merged = compute_exchange_deflator(
            merged,
            exchange="pydeflate_EXCHANGE_to",
            year="pydeflate_year",
            grouper=["pydeflate_entity_code", "pydeflate_iso3"],
        )

        # Drop unnecessary columns
        merged = merged.drop(columns=merged.filter(regex="_to$").columns, axis=1)

        return merged

    def exchange(
        self,
        data: pd.DataFrame,
        value_column: str,
        entity_column: str,
        year_column: str,
        year_format: str = "%Y",
        use_source_codes: bool = False,
    ) -> pd.DataFrame:
        """Apply the exchange rate to the given data to convert it to the target currency.

        Args:
            data (pd.DataFrame): The input DataFrame containing values to be exchanged.
            value_column (str): The column name containing the values to be converted.
            entity_column (str): The column name containing the entity or country codes.
            year_column (str): The column name containing the year information.
            year_format (str, optional): The format of the year (default is '%Y').
            use_source_codes (bool, optional): Whether to use source entity codes
            instead of ISO3 (default is False).

        Returns:
            pd.DataFrame: DataFrame with the values converted to the target currency.
        """

        # Convert the year to an integer
        data["pydeflate_year"] = pd.to_datetime(
            data[year_column], format=year_format
        ).dt.year

        # exchange columns
        exchange_cols = [
            "pydeflate_year",
            "pydeflate_entity_code",
            "pydeflate_iso3",
            "pydeflate_EXCHANGE",
        ]

        # Merge exchange rate data to the input data based on year and entity
        merged_data = data.merge(
            self.exchange_data.filter(exchange_cols),
            how="left",
            left_on=["pydeflate_year", entity_column],
            right_on=[
                "pydeflate_year",
                "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3",
            ],
        )

        # Apply the exchange rate to convert the value column
        merged_data[value_column] = (
            merged_data[value_column] / merged_data["pydeflate_EXCHANGE"]
        )

        # Drop all columns that start with pydeflate_ merging and return the result
        return merged_data.filter(regex="^(?!pydeflate_)")

    def deflator(self) -> pd.DataFrame:
        """Get the exchange rate deflator data.

        Returns:
            pd.DataFrame: DataFrame with the exchange rate deflator data.
        """

        return self.exchange_data.filter(
            [
                "pydeflate_year",
                "pydeflate_entity_code",
                "pydeflate_iso3",
                "pydeflate_EXCHANGE_D",
            ]
        )

    def merge_deflator(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        year_format: str = "%Y",
        use_source_codes: bool = False,
    ) -> pd.DataFrame:
        """Merge the deflator data to the input data based on year and entity.

        Args:
            data (pd.DataFrame): The input DataFrame
            entity_column (str): The column name containing the entity or country codes.
            year_column (str): The column name containing the year information.
            year_format (str, optional): The format of the year (default is '%Y').
            use_source_codes (bool, optional): Whether to use source entity codes
            instead of ISO3 (default is False).

        Returns:
            pd.DataFrame: DataFrame with the deflator data merged to the input data.

        """

        # Convert the year to an integer
        data["pydeflate_year"] = pd.to_datetime(
            data[year_column], format=year_format
        ).dt.year

        # Merge exchange rate data to the input data based on year and entity
        merged_data = data.merge(
            self.deflator(),
            how="left",
            left_on=["pydeflate_year", entity_column],
            right_on=[
                "pydeflate_year",
                "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3",
            ],
        )

        return merged_data.filter(regex="^(?!pydeflate_)")
