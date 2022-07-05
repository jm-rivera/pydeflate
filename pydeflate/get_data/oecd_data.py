import datetime
import io
import warnings
import zipfile as zf
from dataclasses import dataclass
from typing import Union


import pandas as pd

import requests
from bs4 import BeautifulSoup as Bs

from pydeflate.config import PATHS
from pydeflate.get_data.data import Data
from pydeflate.utils import (
    base_year,
    oecd_codes,
    value_index,
    update_update_date,
)

warnings.simplefilter("ignore", Warning, lineno=1013)

_BASE_URL: str = "https://stats.oecd.org/DownloadFiles.aspx?DatasetCode="
_TABLE1_URL: str = f"{_BASE_URL}TABLE1"


def _read_zip_content(request_content: bytes, file_name: str) -> pd.DataFrame:
    """Read the contents of a zip file"""
    _ = io.BytesIO(request_content)
    zip_file = zf.ZipFile(_).open(file_name)

    # Try two alternative separators to read the CSV file
    try:
        return pd.read_csv(zip_file, sep=",", encoding="ISO-8859-1", low_memory=False)

    except UnicodeDecodeError:
        return pd.read_csv(zip_file, sep="|", encoding="ISO-8859-1", low_memory=False)


def _download_bulk_file(url: str) -> bytes:
    """Get zipfile bytes from the webpage"""

    # get URL
    response = requests.get(url)

    # parse html
    page = Bs(response.text, "html.parser")
    link = list(page.find_all("a"))[0].attrs["onclick"][15:-3].replace("_", "-")
    link = f"https://stats.oecd.org/FileView2.aspx?IDFile={link}"

    return requests.get(link).content


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
        df.filter(cols, axis=1)
        .rename(columns=cols)
        .loc[lambda d: d.aid == 1010]  # only Total ODA
        .loc[lambda d: d.flow == 1140]  # only net disbursements
        .filter(["donor_code", "type", "year", "value"])
        .pivot(index=["donor_code", "year"], columns=["type"], values="value")
        .reset_index()
        .assign(
            exchange=lambda d: d.N / d.A,
            deflator=lambda d: (100 * d.A / d.D).round(2),  # implied deflator
            iso_code=lambda d: d.donor_code.map(oecd_codes),
            year=lambda d: pd.to_datetime(d.year, format="%Y"),
        )
        .assign(exchange=lambda d: d.exchange.fillna(1))
        .dropna(subset=["iso_code"])
        .filter(["iso_code", "year", "exchange", "deflator"], axis=1)
    )


def _update_dac1() -> None:
    """Update dac1 data from OECD site and save as feather"""

    file_name = "Table1_Data.csv"

    print("Downloading DAC1 data, which may take a bit")

    zip_bytes = _download_bulk_file(url=_TABLE1_URL)
    df = _read_zip_content(request_content=zip_bytes, file_name=file_name).pipe(
        _clean_dac1
    )
    df.to_feather(PATHS.data + r"/dac1.feather")
    print("Successfully downloaded DAC1 data")
    update_update_date("oecd_dac_data")


@dataclass
class OECD_XE(Data):
    method: Union[str, None] = "implied"
    data: pd.DataFrame = None
    """An object to download and return the latest OECD DAC exchange data"""

    def update(self, **kwargs) -> None:
        _update_dac1()

    def load_data(self, **kwargs) -> None:
        self._check_method()

        self.data = pd.read_feather(
            rf"{PATHS.data}{self.available_methods()[self.method]}"
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
        """The most complete dataset is obtained by deriving the exchange rate
        from the total ODA data found in Table 1"""
        return {"implied": r"/dac1.feather"}

    def get_data(self, currency_iso: str) -> pd.DataFrame:
        """Get an exchange rate for a given ISO"""

        df = self._get_usd_exchange()

        target_xe = self._get_exchange2usd_dict(currency_iso=currency_iso)

        df.value = df.value / df.year.map(target_xe)

        return df

    def get_deflator(self, currency_iso: str) -> pd.DataFrame:
        """get exchange rate deflator based on OECD base year and exchange rates"""

        # get exchange rates
        xe = self.get_data(currency_iso=currency_iso)

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
    """An object to download and return the latest OECD DAC deflators data"""

    def update(self, **kwargs) -> None:
        _update_dac1()

    def load_data(self, **kwargs) -> None:
        self.data = pd.read_feather(PATHS.data + r"/dac1.feather")

    def available_methods(self) -> dict:
        print("Only the DAC Deflators method is available")
        return {"oecd": "OECD DAC Deflator method"}

    def get_data(self) -> pd.DataFrame:
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

    def get_deflator(self, **kwargs) -> pd.DataFrame:
        xe_usd = OECD_XE().get_deflator("USA")

        df = self.get_data().merge(
            xe_usd,
            on=["iso_code", "year"],
            how="left",
            suffixes=("_def", "_xe"),
        )

        df["value"] = round(df.value_def * (df.value_xe / 100), 3)

        return df[["iso_code", "year", "value"]]
