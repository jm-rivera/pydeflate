from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from pydeflate.core.exchange import Exchange
from pydeflate.core.source import Source
from pydeflate.sources.common import AvailableDeflators


@dataclass
class Deflator:
    """A class to manage and process deflator data.

    This class holds deflators and provides methods to apply exchange rates
    for conversions between source and target currencies.

    """

    source: Source | Exchange
    deflator_type: Literal["price", "exchange"]
    price_kind: AvailableDeflators | None
    base_year: int
    deflator_data: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        """Processes the deflator data based on the deflator type.

        Initializes the `deflator_data` attribute by fetching and processing
        the appropriate deflator data from the source.

        Raises:
            ValueError: If the combination of `deflator_type` and `price_kind` is invalid.
        """

        # If price deflator, fetch the price deflator data
        if self.deflator_type == "price":
            if self.price_kind is None:
                raise ValueError(
                    "`price_kind` must be specified when `deflator_type` is 'price'."
                )
            self.deflator_data = self.source.price_deflator(kind=self.price_kind)

        # If exchange deflator, fetch the exchange deflator data
        elif self.deflator_type == "exchange":
            if self.price_kind is not None:
                raise ValueError(
                    "`price_kind` should be None when `deflator_type` is 'exchange'."
                )
            self.deflator_data = self.source.deflator()
            self.source = self.source.source

        else:
            raise ValueError(f"Invalid deflator type: {self.deflator_type}")

        # Rebase the deflator data to the specified base year
        self.rebase_deflator()

    def _extract_base_year_values(self, value_column: str) -> pd.DataFrame:
        """Extracts the base year values from the deflator data."""

        # Extract base year values
        base_year_values = (
            self.deflator_data[self.deflator_data["pydeflate_year"] == self.base_year]
            .rename(columns={value_column: "base_year_value"})
            .drop(columns=["pydeflate_year"])
        )

        if base_year_values.empty:
            raise ValueError(f"No data found for base year {self.base_year}.")
        return base_year_values

    @staticmethod
    def _ensure_deflator_suffix(value_column: str) -> str:
        """Ensures that the value column ends with the '_D' suffix."""
        return value_column if value_column.endswith("_D") else value_column + "_D"

    def _get_deflator_value_column(self) -> str:
        """Identifies the value column in the deflator data."""
        # Identify the value column
        value_column = self.deflator_data.columns.difference(self.source._idx).tolist()

        if len(value_column) != 1:
            raise ValueError("Invalid deflator data format.")

        return value_column[0]

    def rebase_deflator(self) -> None:
        """Rebases the deflator data to the specified base year.

        Adjusts the deflator values so that the base year values are set to 100.

        Raises:
            ValueError: If `deflator_data` is empty, has an invalid format, or lacks data for the base year.
        """

        # Check if deflator data is empty
        if self.deflator_data.empty:
            raise ValueError("No deflator data found.")

        # Identify the value column
        value_column = self._get_deflator_value_column()

        # Extract base year values
        base_year_values = self._extract_base_year_values(value_column)

        # Merge base year values back into the main DataFrame
        rebased = self.deflator_data.merge(
            base_year_values,
            on=[c for c in self.source._idx if c != "pydeflate_year"],
            how="left",
        )

        # if value column doesn't end in _D, add it
        original_value_column = value_column
        value_column = self._ensure_deflator_suffix(value_column)

        # Rebase the deflator values
        rebased[value_column] = (
            100 * rebased[original_value_column] / rebased["base_year_value"]
        ).round(6)

        # Update the deflator data
        self.deflator_data = rebased.drop(columns=["base_year_value"])


class ExchangeDeflator(Deflator):
    """Manages and processes exchange rate deflators.

    Using exchange rate data (local currency to USD) provided by the source.
    It normalizes exchange rate deflators to a specified base year, allowing
    consistent comparisons over time.

    Args:
        source (Source): The source from which to fetch exchange rate data.
        base_year (int): The base year to rebase the deflator data.
    """

    def __init__(self, source: Exchange, base_year: int):
        super().__init__(
            source=source,
            deflator_type="exchange",
            price_kind=None,
            base_year=base_year,
        )


class PriceDeflator(Deflator):
    """Manages and processes price deflators data.

    It fetches price deflator data from the provided source and normalizes it to a specified
    base year, allowing for inflation-adjusted comparisons over time.

    Args:
        source (Source): The source from which to fetch price deflator data.
        kind (AvailableDeflators): The type of price deflator to apply (e.g., GDP deflator or CPI).
        base_year (int): The base year to rebase the deflator data.
    """

    def __init__(
        self,
        source: Source,
        kind: AvailableDeflators,
        base_year: int,
    ):
        super().__init__(
            source=source,
            deflator_type="price",
            price_kind=kind,
            base_year=base_year,
        )
