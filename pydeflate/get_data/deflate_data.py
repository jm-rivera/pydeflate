from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class Data(ABC):
    _data: pd.DataFrame | None = None
    _available_methods: dict | None = None
    """Abstract class defining the basic structure and functionality of Data classes.
    
    Data classes store the price data from different sources.
    """

    @abstractmethod
    def update(self, **kwargs) -> None:
        """Update underlying data"""

    @abstractmethod
    def load_data(self, **kwargs) -> None:
        """Load required data to construct deflator"""

    def available_methods(self) -> dict:
        """Return a dictionary of available methods with their functions"""
        return self._available_methods

    def get_method(self, method: str) -> pd.DataFrame:
        """Return the data for a given method"""
        if self._data is None:
            self.load_data()

        if method not in self._data.indicator.unique():
            raise ValueError(f"Invalid method {method=}")

        return (
            self._data.loc[lambda d: d.indicator == method]
            .filter(["iso_code", "year", "value"], axis=1)
            .sort_values(["iso_code", "year"])
            .reset_index(drop=True)
        )

    def get_deflator(self, base_year: int, method: str | None = None) -> pd.DataFrame:
        if method is None:
            raise ValueError("method must be specified")

        if method not in self.available_methods():
            raise ValueError(f"method must be one of {self.available_methods().keys()}")

        if self._data is None:
            self.load_data()

        d_ = self.get_method(self._available_methods[method])

        # get the data for the selected base year.
        d_base = d_.query(f"year.dt.year == {base_year}")

        # If base year is not valid, raise error
        if len(d_base) == 0:
            raise ValueError(f"No currency exchange data for {base_year=}")

        # Merge the exchange data and the base year data
        d_ = d_.merge(d_base, how="left", on=["iso_code"], suffixes=("", "_base"))

        # Calculate the deflator
        d_.value = round(100 * d_.value / d_.value_base, 6)

        return d_.filter(["iso_code", "year", "value"], axis=1)
