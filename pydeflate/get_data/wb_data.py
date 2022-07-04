from dataclasses import dataclass
from typing import Union

import pandas as pd
from pandas_datareader import wb

from pydeflate import config
from pydeflate.get_data.data import Data
from pydeflate.utils import emu, value_index, update_update_date

_INDICATORS: dict = {
    "gdp": "NY.GDP.DEFL.ZS",
    "gdp_linked": "NY.GDP.DEFL.ZS.AD",
    "cpi": "FP.CPI.TOTL",
    "exchange": "PA.NUS.FCRF",
    "effective_exchange": "PX.REX.REER",
}

START: int = 1950
END: int = 2025


def _download_wb_indicator(indicator: str, start: int, end: int) -> None:
    """Download an indicator from WB (caching if applicable)"""

    df = (
        wb.WorldBankReader(
            symbols=indicator,
            countries="all",
            start=start,
            end=end,
        )
        .read()
        .reset_index(drop=False)
    )

    countries = wb.get_countries()
    countries[["name", "iso3c"]].to_csv(
        config.PATHS.data + rf"/wb_class.csv", index=False
    )

    df.to_feather(config.PATHS.data + rf"/{indicator}_{start}_{end}.feather")
    print(f"Successfully updated {indicator} for {start}-{end}")
    update_update_date("wb")


def _get_iso3c():
    countries = pd.read_csv(config.PATHS.data + rf"/wb_class.csv")
    return countries[["name", "iso3c"]].set_index("name")["iso3c"].to_dict()


def _clean_wb_indicator(
    data: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:
    """Add iso_code, change value name to value and sort"""

    return (
        data.assign(
            iso_code=lambda d: d.country.map(_get_iso3c()),
            year=lambda d: pd.to_datetime(d.year, format="%Y"),
        )
        .rename(columns={indicator: "value"})
        .dropna(subset=["iso_code"])
        .sort_values(["iso_code", "year"])
        .reset_index(drop=True)
        .filter(["year", "iso_code", "value"], axis=1)
    )


@dataclass
class WB_XE(Data):
    method: Union[str, None] = "exchange"
    data: pd.DataFrame = None

    def update(self, **kwargs) -> None:
        _ = [
            _download_wb_indicator(i, START, END)
            for i in self.available_methods().values()
        ]

    def load_data(self, **kwargs) -> None:
        self._check_method()
        indicator = _INDICATORS[self.method]

        self.data = pd.read_feather(
            config.PATHS.data + rf"/{indicator}_{START}_{END}.feather"
        ).pipe(_clean_wb_indicator, indicator)

    def available_methods(self) -> dict:
        return {
            k: v
            for k, v in _INDICATORS.items()
            if k in ["exchange", "effective_exchange"]
        }

    def _get_usd_exchange(self) -> pd.DataFrame:
        """Official exchange rate refers to the exchange rate determined by
        national authorities or to the rate determined in the legally
        sanctioned exchange market. It is calculated as an annual average based on
        monthly averages (local currency units relative to the U.S. dollar)."""

        # get exchange rates
        if self.data is None:
            self.load_data()

        df = self.data

        eur = df.loc[df.iso_code == "EMU"].dropna().set_index("year")["value"].to_dict()

        # Euro area countries without exchange rates
        eur_mask = (df.iso_code.isin(emu)) & (df.value.isna())

        # Assign EURO exchange rate to euro are countries from year euro adopted
        df.loc[eur_mask, "value"] = df.year.map(eur)

        return df

    def _get_exchange2usd_dict(self, currency_iso: str) -> dict:
        """Dictionary of currency_iso to USD"""

        df = self._get_usd_exchange()

        return (
            df.loc[df.iso_code == currency_iso]
            .dropna()
            .set_index("year")["value"]
            .to_dict()
        )

    def _get_euro2usd(self) -> dict:
        """Dictionary of EUR to USD exchange rates"""

        return self._get_exchange2usd_dict(currency_iso="EMU")

    def _get_can2usd(self) -> dict:
        """Dictionary of CAN to USD exchange rates"""

        return self._get_exchange2usd_dict(currency_iso="CAN")

    def _get_gbp2usd(self) -> dict:
        """Dictionary of GBP to USD exchange rates"""

        return self._get_exchange2usd_dict(currency_iso="GBR")

    def get_data(self, currency_iso: str) -> pd.DataFrame:
        """Get exchange rates based on a given currency/country (from LCU)"""
        # Get WB exchange rates
        df = self._get_usd_exchange()
        target_xe = self._get_exchange2usd_dict(currency_iso=currency_iso)

        df.value = df.value / df.year.map(target_xe)

        return df

    def get_deflator(
        self, currency_iso: str = "USA", base_year: int = 2010
    ) -> pd.DataFrame:
        from datetime import datetime

        # get exchange rates
        xe = self.get_data(currency_iso=currency_iso)

        # get deflators and base year
        base = {iso: datetime(base_year, 1, 1) for iso in xe.iso_code.unique()}

        # get the exchange rate as an index based on the base year
        xe.value = value_index(xe, base)

        return xe


@dataclass
class WB(Data):
    method: Union[str, None] = None
    data: pd.DataFrame = None
    """An object to download and return the latest WB exchange and price data"""

    def update(self, **kwargs) -> None:
        """Update data for all WB indicators"""

        _ = [_download_wb_indicator(i, START, END) for i in _INDICATORS.values()]

    def load_data(
        self,
        indicator: str,
    ) -> None:
        self.data = pd.read_feather(
            config.PATHS.data + rf"/{indicator}_{START}_{END}.feather"
        ).pipe(_clean_wb_indicator, indicator)

    def available_methods(self) -> dict:
        return {
            k: v
            for k, v in _INDICATORS.items()
            if k not in ["exchange", "effective_exchange"]
        }

    def _get_indicator(self) -> pd.DataFrame:
        self._check_method()
        indicator = _INDICATORS[self.method]

        if self.data is None:
            self.load_data(indicator=indicator)

        return self.data

    def get_data(self):
        raise NotImplementedError

    def get_deflator(self, **kwargs) -> pd.DataFrame:
        return self._get_indicator()
