from dataclasses import dataclass, field

import pandas as pd

from pydeflate.sources.common import compute_exchange_deflator
from pydeflate.sources.imf import read_weo


@dataclass
class Exchange:
    """A class to manage and process exchange rate data for currency conversions.

    This class holds exchange rate data and provides methods to apply exchange rates
    for conversions between source and target currencies.

    Attributes:
        name (str): The name of the exchange rate data source (e.g., "World Bank").
        reader (callable): A function that reads the exchange rate data.
        source_currency (str): The source currency code (default is 'LCU' - Local Currency Unit).
        target_currency (str): The target currency code (default is 'USA' - US Dollar).
        update (bool): Flag to indicate if the exchange data should be updated (default: False).
        exchange_data (pd.DataFrame): DataFrame holding the exchange rate data.
    """

    name: str
    reader: callable
    source_currency: str = "LCU"
    target_currency: str = "USA"
    update: bool = False
    exchange_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    _raw_data: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        """Initialize the Exchange object and process the exchange rate data."""
        # Load and filter the relevant columns from the exchange rate data
        self._raw_data = self.reader(self.update).filter(
            [
                "pydeflate_year",
                "pydeflate_entity_code",
                "pydeflate_iso3",
                "pydeflate_EXCHANGE",
                "pydeflate_EXCHANGE_D",
            ]
        )

        # Handle cases where EUR is represented differently in the World Bank data
        if self.name == "World Bank":
            self._raw_data["pydeflate_iso3"] = self._raw_data["pydeflate_iso3"].replace(
                {"EMU": "EUR"}
            )

        # Assign data to exchange_data
        self.exchange_data = self._raw_data.copy()

        # If source and target currencies are the same, set the exchange rate to 1
        if self.source_currency == self.target_currency:
            self.exchange_data["pydeflate_EXCHANGE"] = 1
            self.exchange_data["pydeflate_EXCHANGE_D"] = 1

        # Convert exchange rates if the source currency is not LCU
        if self.source_currency != "LCU":
            self._convert_exchange(self.source_currency)

        # Convert exchange rates if the target currency is not USA or LCU
        if self.target_currency != "LCU":
            self._convert_exchange(self.target_currency)

        # If target currency is LCU, invert the exchange rates to match the local currency unit
        if self.target_currency == "LCU":
            self.exchange_data["pydeflate_EXCHANGE"] = (
                1 / self.exchange_data["pydeflate_EXCHANGE"]
            )

        self.exchange_data = compute_exchange_deflator(
            self.exchange_data,
            base_year_measure="pydeflate_EXCHANGE_D",
            exchange="pydeflate_EXCHANGE",
            year="pydeflate_year",
            grouper=["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"],
        )

    def _convert_exchange(self, to_currency: str):
        """Convert exchange rates to a specified target currency.

        Args:
            to_currency (str): The currency code to which the exchange rates should be converted.

        Returns:
            pd.DataFrame: DataFrame with converted exchange rates.
        """
        currency = self._raw_data.loc[lambda d: d["pydeflate_iso3"] == to_currency]

        # Merge the exchange rates to the original DataFrame and calculate the conversion
        self.exchange_data = (
            self.exchange_data.merge(
                currency.filter(["pydeflate_year", "pydeflate_EXCHANGE"]),
                on="pydeflate_year",
                suffixes=("", "_to"),
            )
            .assign(
                pydeflate_EXCHANGE=lambda d: d["pydeflate_EXCHANGE"]
                / d["pydeflate_EXCHANGE_to"]
            )
            .drop(columns=["pydeflate_EXCHANGE_to"])
        )

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


if __name__ == "__main__":
    weo = Exchange(
        name="WEO",
        reader=read_weo,
        source_currency="FRA",
        target_currency="USA",
    )

    d = weo.exchange_data.query("pydeflate_iso3=='FRA'")
