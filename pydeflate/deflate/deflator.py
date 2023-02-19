"""Defines the deflator class"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pydeflate.get_data.deflate_data import Data
from pydeflate.get_data.exchange_data import Exchange


@dataclass
class Deflator:
    base_year: int
    exchange_obj: Exchange
    deflator_obj: Data
    deflator_method: str
    source_currency: str = "LCU"
    target_currency: str = "USA"
    to_current: bool = False
    _xe_df: pd.DataFrame | None = None
    _xe_deflator_df: pd.DataFrame | None = None
    _price_deflator_df: pd.DataFrame | None = None
    """A class to produce deflators based on the given parameters.
    
    Deflators take into account changes in prices and the evolution of currency exchange
    values. They compensate for both factors in order to produce a standard unit of 
    measurement, regardless of the year of the flow.
    
    Args:
        base_year: the year in which the deflator equals 100 (if the source and target
        currency are equal).
        Exchange: the exchange rate object.
        price: the price data oject.
        source_currency: the ISO3 code of the country which uses the source currency
        target_currency: the ISO3 code of the country which used the target currency
        _deflator_df: the resulting DataFrame containing the deflators data.
    """

    def __post_init__(self):
        # Exchange deflator DataFrame, including any currency conversion
        self._xe_deflator_df = self.exchange_obj.exchange_deflator(
            source_iso=self.source_currency,
            target_iso=self.target_currency,
            base_year=self.base_year,
        )

        # Price deflator DataFrame
        self._price_deflator_df = self.deflator_obj.get_deflator(
            base_year=self.base_year, method=self.deflator_method
        )

    def get_deflator(self) -> pd.DataFrame:
        """Get the deflator DataFrame"""

        # Merge the price and currency exchange deflators
        df = self._price_deflator_df.merge(
            self._xe_deflator_df,
            on=["iso_code", "year"],
            how="left",
            suffixes=("_def", "_xe"),
        )

        # Calculate the deflator
        df = (
            df.assign(
                value=round(100 * df.value_def / df.value_xe, 6)
                if not self.to_current
                else round(100 * df.value_xe / df.value_def, 6)
            )
            .filter(["iso_code", "year", "value"], axis=1)
            .assign(value=lambda d: d.value.replace(0, np.nan))
            .dropna(subset=["value"])
            .reset_index(drop=True)
            .rename(columns={"value": "deflator"})
        )

        return df
