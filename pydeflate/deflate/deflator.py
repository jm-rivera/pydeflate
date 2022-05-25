"""Define the deflator class"""

from dataclasses import dataclass
from typing import Union, Callable


import pandas as pd

from pydeflate import utils


@dataclass
class Deflator:
    base_year: int
    xe_deflator: Callable
    price_deflator: Callable
    xe: pd.DataFrame
    source_currency: str = "LCU"
    target_currency: str = "USA"
    deflator_df: Union[None, pd.DataFrame] = None

    def __align_currencies(
        self, deflator: pd.DataFrame, xe: pd.DataFrame,
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

    def _defl_pipeline(self,) -> pd.DataFrame:

        """Returns a dataframe with price-currency deflators.
        -exchange_deflator takes in a Callable to get exchange rate deflators.
        -price_deflator takes in a Callable to get gdp/price deflators.
        -base_year takes an integer as the base year for the deflators.
        """

        # get exchange rate and rebase
        xed = self._get_and_deflate(func=self.xe_deflator)

        # get price deflators and rebase
        prd = self._get_and_deflate(func=self.price_deflator)

        df = prd.merge(
            xed, on=["iso_code", "year"], how="left", suffixes=("_def", "_xe")
        )

        df["value"] = round(100 * df.value_def / df.value_xe, 2)

        return (
            df.filter(["iso_code", "year", "value"], axis=1)
            .replace(0, pd.NA)
            .dropna(subset=["value"])
            .reset_index(drop=True)
            .pipe(self.__align_currencies, xe=self.xe)
            .rename(columns={"value": "deflator"})
        )

    def _set_deflator_df(self, df: pd.DataFrame) -> None:
        self.deflator_df = df

    def deflator(self) -> pd.DataFrame:
        self._defl_pipeline().pipe(self._set_deflator_df)

        return self.deflator_df
