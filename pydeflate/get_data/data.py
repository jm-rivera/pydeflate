from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
import pandas as pd


@dataclass
class Data(ABC):
    method: Union[str, None]
    data: pd.DataFrame

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
        pass

    def set_method(self, method:str) -> None:
        self.method = method

    @abstractmethod
    def get_deflator(self) -> pd.DataFrame:
        pass
