from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class Data(ABC):
    data: pd.DataFrame | None = None
    _tries: int = 0
    _file: pd.DataFrame | None = None
    """Abstract class defining the basic structure and functionality of Data classes.
    
    Data classes store the price data from different sources.
    """

    @abstractmethod
    def update(self, **kwargs) -> None:
        """Update underlying data"""

    @abstractmethod
    def load_data(self, **kwargs) -> None:
        """Load required data to construct deflator"""

    @abstractmethod
    def get_data(self, **kwargs) -> pd.DataFrame:
        """Get the data as a dataframe"""
