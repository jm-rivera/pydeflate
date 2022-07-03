from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

import pandas as pd


@dataclass
class Data(ABC):
    method: Union[str, None]
    data: pd.DataFrame
    """Abstract class defining the basic structure and functionality of Data classes.
    Data classes store the price or exchange data from different sources."""

    @abstractmethod
    def update(self, **kwargs) -> None:
        """Update underlying data"""
        pass

    @abstractmethod
    def load_data(self, **kwargs) -> None:
        """Load required data to construct deflator"""
        pass

    @abstractmethod
    def available_methods(self) -> dict:
        """Return a dictionary of available methods with their functions"""
        pass

    def _check_method(self) -> None:
        if self.method is None:
            raise AttributeError(
                f"`method` must be defined: " f"{list(self.available_methods().keys())}"
            )

    def set_method(self, method: str) -> Data:
        self.method = method
        return self

    @abstractmethod
    def get_data(self, **kwargs) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_deflator(self, **kwargs) -> pd.DataFrame:
        pass
