#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime
import io
import warnings
import zipfile as zf
from dataclasses import dataclass
from typing import Union
from urllib.error import HTTPError

import pandas as pd
import requests
from bs4 import BeautifulSoup as Bs

from pydeflate.config import paths
from pydeflate.get_data.data import Data
from pydeflate.utils import base_year, oecd_codes, value_index, update_update_date

warnings.simplefilter("ignore", Warning, lineno=1013)

_BASE_URL: str = "https://stats.oecd.org/DownloadFiles.aspx?DatasetCode="
_TABLE1_URL: str = f"{_BASE_URL}TABLE1"


def _get_zip(url):
    """Get Zip File."""

    try:
        return requests.get(url)

    except ConnectionError:
        raise ConnectionError("Could not download file")


def _read_zip_content(request_content, file_name: str) -> pd.DataFrame:
    # Read zip as content
    _ = io.BytesIO(request_content)
    zip_file = zf.ZipFile(_).open(file_name)

    try:
        return pd.read_csv(zip_file, sep=",", encoding="ISO-8859-1", low_memory=False)

    except UnicodeDecodeError:
        return pd.read_csv(zip_file, sep="|", encoding="ISO-8859-1", low_memory=False)


def _download_bulk_file(url: str, file_name: str) -> pd.DataFrame:
    # get URL
    response = requests.get(url)

    # parse html
    soup = Bs(response.text, "html.parser")
    link = list(soup.find_all("a"))[0].attrs["onclick"][15:-3].replace("_", "-")
    link = f"https://stats.oecd.org/FileView2.aspx?IDFile={link}"

    file_content = _get_zip(link).content

    return _read_zip_content(request_content=file_content, file_name=file_name)


def _update_dac_deflators() -> None:
    """Update DAC deflators data to latest base year"""

    year = datetime.datetime.now().year

    t = True

    while t:
        url = (
            f"https://www.oecd.org/dac/financing-sustainable-development/"
            f"development-finance-data/Deflators-base-{year}.xls"
        )

        try:
            df = pd.read_excel(url, header=2)
            df = df.dropna(how="all")
            df.to_csv(paths.data + r"/dac_deflators.csv", index=False)
            print(f"Updated OECD DAC deflators {year}")
            update_update_date("oecd_dac_deflator")
            t = False

        except HTTPError:
            year -= 1


def _update_dac_exchange() -> None:
    """Update DAC Exchange rates to latest available"""

    try:
        exchange = (
            "https://www.oecd.org/dac/financing-sustainable-development/"
            "development-finance-data/Exchange-rates.xls"
        )

        df = pd.read_excel(exchange, header=2)
        df.to_csv(paths.data + r"/dac_exchange_rates.csv", index=False)
        print("Updated OECD DAC exchange rates")
        update_update_date("oecd_dac_exchange")

    except HTTPError:
        print("Error downloading new exchange rates")


def _clean_dac1(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DAC1 to keep only relevant information for deflators and exchange"""

    cols = {
        "DONOR": "donor_code",
        "AMOUNTTYPE": "type",
        "AIDTYPE": "aid",
        "Year": "year",
        "FLOWS": "flow",
        "Value": "value",
    }

    return (
        df.filter(cols.keys(), axis=1)
        .rename(columns=cols)
        .loc[lambda d: d.aid == 1010]  # only Total ODA
        .loc[lambda d: d.flow == 1140]  # only net disbursements
        .filter(["donor_code", "type", "year", "value"])
        .pivot(index=["donor_code", "year"], columns=["type"], values="value")
        .reset_index()
        .assign(
            exchange=lambda d: d.N / d.A,
            deflator=lambda d: (100 * d.A / d.D).round(2),
            iso_code=lambda d: d.donor_code.map(oecd_codes),
            year=lambda d: pd.to_datetime(d.year, format="%Y"),
        )
        .dropna(subset=["iso_code"])
        .filter(["iso_code", "year", "exchange", "deflator"], axis=1)
    )


def _update_dac1() -> None:
    """Update dac1 data from OECD site and save as feather"""

    file_name = "Table1_Data.csv"

    print("Downloading DAC1 data, which may take a bit")
    df = _download_bulk_file(url=_TABLE1_URL, file_name=file_name).pipe(_clean_dac1)
    df.to_feather(paths.data + r"/dac1.feather")
    print("Successfully downloaded DAC1 data")
    update_update_date("oecd_dac_data")


def get_gdp_deflator(dac_deflator, usd_xe_deflator) -> pd.DataFrame:
    """Deduce prices deflator based on exchange rate deflators and DAC
    deflators data"""

    df = dac_deflator.merge(
        usd_xe_deflator, on=["iso_code", "year"], how="left", suffixes=("_def", "_xe"),
    )

    df["value"] = round(df.value_def * (df.value_xe / 100), 3)

    return df[["iso_code", "year", "value"]]


@dataclass
class OECD_XE(Data):
    method: Union[str, None] = "implied"
    data: pd.DataFrame = None

    def update(self, **kwargs) -> None:
        _update_dac_exchange()

    def load_data(self, **kwargs) -> None:
        self._check_method()
        self.data = pd.read_feather(
            rf"{paths.data}{self.available_methods()[self.method]}"
        )

    def _get_usd_exchange(self) -> pd.DataFrame:
        if self.data is None:
            self.load_data()

        return self.data[["iso_code", "year", "exchange"]].rename(
            columns={"exchange": "value"}
        )

    def _get_exchange2usd_dict(self, currency_iso: str) -> dict:
        """Dictionary of currency_iso to USD"""

        df = self._get_usd_exchange()

        return (
            df.loc[df.iso_code == currency_iso]
            .dropna()
            .set_index("year")["value"]
            .to_dict()
        )

    def available_methods(self) -> dict:
        return {"implied": r"/dac1.feather", "official": r"/dac_exchange_rates.csv"}

    def get_exchange_rate(self, currency_iso: str) -> pd.DataFrame:
        """Get an exchange rate for a given ISO"""

        df = self._get_usd_exchange()

        target_xe = self._get_exchange2usd_dict(currency_iso=currency_iso)

        df.value = df.value / df.year.map(target_xe)

        return df

    def get_deflator(self, currency_iso: str) -> pd.DataFrame:
        """get exchange rate deflator based on OECD base year and exchange rates"""

        # get exchange rates
        xe = self.get_exchange_rate(currency_iso=currency_iso)

        # If currency is not valid
        if int(xe.value.sum()) == 0:
            raise ValueError(f"No currency exchange data for {currency_iso}")

        # get deflators and base year
        defl = self.data[["iso_code", "year", "deflator"]].rename(
            columns={"deflator": "value"}
        )

        base = base_year(defl, "year")

        # get the exchange rate as an index based on the base year
        xe.value = value_index(xe, base)

        return xe


@dataclass
class OECD(Data):
    method: Union[str, None] = None
    data: pd.DataFrame = None

    def update(self, **kwargs) -> None:
        _update_dac1()
        _update_dac_deflators()

    def load_data(self, **kwargs) -> None:
        self.data = pd.read_feather(paths.data + r"/dac1.feather")

    def available_methods(self) -> dict:
        print("Only the DAC Deflators method is available")
        return {"oecd": "OECD DAC Deflator method"}

    def get_deflator(self) -> pd.DataFrame:
        if self.data is None:
            self.load_data()

        if self.method is not None:
            print(
                "Only the DAC Deflators method is available.\n"
                f"'Method {self.method}' ignored"
            )

        return self.data[["iso_code", "year", "deflator"]].rename(
            columns={"deflator": "value"}
        )


if __name__ == "__main__":
    oecd_deflator = OECD().get_deflator()
    oecd_xe = OECD_XE().get_exchange_rate('FRA')
