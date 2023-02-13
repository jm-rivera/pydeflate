"""Defines the deflator class"""

from dataclasses import dataclass
from typing import Union, Callable

import numpy as np
import pandas as pd

from pydeflate import utils
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
        # Exchange DataFrame
        iso = self.source_currency if self.to_current else self.target_currency
        self._xe_df = self.exchange_obj.exchange_rate(currency_iso=iso)

        # Exchange deflator DataFrame
        self._xe_deflator_df = self.exchange_obj.exchange_deflator(
            "LCU", target_iso=iso, base_year=self.base_year
            )

        # Deflator DataFrame
        self._price_deflator_df = self.deflator_obj.get_deflator(
            base_year=self.base_year, method=self.deflator_method
        )

    def _align_currencies(self, deflator: pd.DataFrame) -> pd.DataFrame:
        """Check whether an exchange rate needs to be applied to a deflator set
        in order to properly convert data from source to target currency"""

        # If both the source and target currency match, do nothing
        if self.source_currency == self.target_currency:
            return deflator

        if self.source_currency == "LCU":
            deflator = deflator.merge(
                self._xe_df, on=["iso_code", "year"], suffixes=("", "_xe")
            )
            deflator.value = deflator.value * deflator.value_xe
        else:
            xe = self._xe_df.loc[lambda d: d.iso_code == self.source_currency].drop(
                columns=["iso_code"]
            )
            deflator = deflator.merge(xe, on=["year"], suffixes=("", "_xe"))
            deflator.value = deflator.value * deflator.value_xe

        # Check if data is valid
        if int(deflator.value_xe.sum()) == 0:
            raise ValueError(f"Data for {self.source_currency} is not valid")

        return deflator.drop("value_xe", axis=1)

    def get_deflator(self) -> pd.DataFrame:
        """Get the deflator DataFrame"""
        df = self._price_deflator_df.merge(
            self._xe_deflator_df,
            on=["iso_code", "year"],
            how="left",
            suffixes=("_def", "_xe"),
        )

        df = (
            df.assign(value=round(100 * df.value_def / df.value_xe, 6))
            .filter(["iso_code", "year", "value"], axis=1)
            .assign(value=lambda d: d.value.replace(0, np.nan))
            .dropna(subset=["value"])
            .reset_index(drop=True)
            .pipe(self._align_currencies)
            .rename(columns={"value": "deflator"})
        )

        return df


@dataclass
class OldDeflator:
    base_year: int
    xe_deflator: Callable
    price_deflator: Callable
    xe: pd.DataFrame
    source_currency: str = "LCU"
    target_currency: str = "USA"
    deflator_df: Union[None, pd.DataFrame] = None

    """A class to produce deflators based on the given parameters.
    
    Deflators take into account changes in prices and the evolution of currency exchange
    values. They compensate for both factors in order to produce a standard unit of 
    measurement, regardless of the year of the flow.
    
    Args:
        base_year: the year in which the delfator equals 100 (if the source and target
        currency are equal).
        xe_deflator: the exchange rate deflator function to be used.
        price_deflator: the price deflator function to be used.
        xe: exchange rate information used in producing the deflators
        source_currency: the ISO3 code of the country which uses the source currency
        target_currency: the ISO3 code of the country which used the target currency
        deflator_df: the resulting DataFrame containing the deflators data.
    """

    def __align_currencies(
        self,
        deflator: pd.DataFrame,
        xe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Check whether an exchange rate needs to be applied to a deflator set
        in order to properly convert data from source to target currency"""

        # If both the source and target currency match, do nothing
        if self.source_currency == self.target_currency:
            return deflator

        if self.source_currency == "LCU":
            deflator = deflator.merge(xe, on=["iso_code", "year"], suffixes=("", "_xe"))
            deflator.value = deflator.value * deflator.value_xe
        else:
            xe = xe.loc[xe.iso_code == self.source_currency]
            deflator = deflator.merge(
                xe.drop("iso_code", axis=1), on=["year"], suffixes=("", "_xe")
            )
            deflator.value = deflator.value * deflator.value_xe

        # Check if data is valid
        if int(deflator.value_xe.sum()) == 0:
            raise ValueError(f"Data for {self.source_currency} is not valid")

        return deflator.drop("value_xe", axis=1)

    def _get_and_deflate(self, func: Callable):
        if self.target_currency is None:
            df = func()
        else:
            df = func(currency_iso=self.target_currency)

        if self.base_year not in set(df.year.dt.year):
            raise ValueError(f"Base year ({self.base_year} not valid.")

        df["value"] = utils.rebase(df, self.base_year)

        return df

    def _defl_pipeline(
        self,
    ) -> pd.DataFrame:
        """Returns a dataframe with price-currency deflators."""

        # get exchange rate and rebase
        xed = self._get_and_deflate(func=self.xe_deflator)

        # get price deflators and rebase
        prd = self._get_and_deflate(func=self.price_deflator)

        df = prd.merge(
            xed, on=["iso_code", "year"], how="left", suffixes=("_def", "_xe")
        )

        df["value"] = round(100 * df.value_def / df.value_xe, 6)

        return (
            df.filter(["iso_code", "year", "value"], axis=1)
            .assign(value=lambda d: d.value.replace(0, np.nan))
            .dropna(subset=["value"])
            .reset_index(drop=True)
            .pipe(self.__align_currencies, xe=self.xe)
            .rename(columns={"value": "deflator"})
        )

    def _set_deflator_df(self, df: pd.DataFrame) -> None:
        self.deflator_df = df

    def deflator(self) -> pd.DataFrame:
        """Execute the pipeline to create the deflators. It uses the information
        passed when creating the Deflator object"""
        self._defl_pipeline().pipe(self._set_deflator_df)

        return self.deflator_df
