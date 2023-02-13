import io
import warnings
import zipfile as zf
from dataclasses import dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup as Bs

from pydeflate.get_data.deflate_data import Data
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.utils import oecd_codes, update_update_date

warnings.simplefilter("ignore", Warning, lineno=1013)

_BASE_URL: str = "https://stats.oecd.org/DownloadFiles.aspx?DatasetCode="
_TABLE1_URL: str = f"{_BASE_URL}TABLE1"


def _read_zip_content(request_content: bytes, file_name: str) -> pd.DataFrame:
    """Read the contents of a zip file

    Args:
        request_content: the content of the request
        file_name: the name of the file to read.

    Returns:
        A pandas dataframe with the contents of the file

    """
    # Read the zipfile
    _ = io.BytesIO(request_content)
    zip_file = zf.ZipFile(_).open(file_name)

    # Try two alternative separators to read the CSV file
    try:
        return pd.read_csv(zip_file, sep=",", encoding="ISO-8859-1", low_memory=False)

    except UnicodeDecodeError:
        return pd.read_csv(zip_file, sep="|", encoding="ISO-8859-1", low_memory=False)


def _download_bulk_file(url: str) -> bytes:
    """Get zipfile bytes from the webpage

    Args:
        url: the url to download the file from

    Returns:
        The content of the file (bytes)

    """

    # get URL
    response = requests.get(url)

    # parse html
    page = Bs(response.text, "html.parser")
    link = list(page.find_all("a"))[0].attrs["onclick"][15:-3].replace("_", "-")
    link = f"https://stats.oecd.org/FileView2.aspx?IDFile={link}"

    return requests.get(link).content


def _clean_dac1(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DAC1 to keep only relevant information for deflators and exchange.

    Args:
        df: the dataframe to clean

    Returns:
        A cleaned dataframe
    """

    # Columns to keep and rename
    cols = {
        "DONOR": "donor_code",
        "AMOUNTTYPE": "type",
        "AIDTYPE": "aid",
        "Year": "year",
        "FLOWS": "flow",
        "Value": "value",
    }

    # Get only the official definition of the data
    query = (
        "(aid == 1010 & flow == 1140 & year <2018 ) | "
        "(aid == 11010 & flow == 1160 & year >=2018)"
    )

    # Clean the data
    data = (
        df.filter(cols, axis=1)
        .rename(columns=cols)
        .astype({"year": "Int32"})
        .query(query)
        .filter(["donor_code", "type", "year", "value"])
        .pivot(index=["donor_code", "year"], columns=["type"], values="value")
        .reset_index()
        .assign(
            exchange=lambda d: round(d.N / d.A, 5),
            deflator=lambda d: round(100 * d.A / d.D, 6),  # implied deflator
            iso_code=lambda d: d.donor_code.map(oecd_codes()),
            year=lambda d: pd.to_datetime(d.year, format="%Y"),
        )
        .assign(exchange=lambda d: d.exchange.fillna(1))
        .dropna(subset=["iso_code"])
        .filter(["iso_code", "year", "exchange", "deflator"], axis=1)
    )

    return data


def _update_dac1() -> None:
    """Update dac1 data from OECD site and save as feather"""

    logger.info("Downloading DAC1 data, which may take a bit")

    # File name to read
    file_name = "Table1_Data.csv"

    # Download the zip bytes
    zip_bytes = _download_bulk_file(url=_TABLE1_URL)

    # Read the zip file and clean the data
    df = (
        _read_zip_content(request_content=zip_bytes, file_name=file_name)
        .pipe(_clean_dac1)
        .reset_index(drop=True)
    )

    # Save the data
    df.to_feather(PYDEFLATE_PATHS.data / "dac1.feather")

    # Update the update date
    update_update_date("oecd_dac_data")

    # Log
    logger.info("Successfully downloaded DAC1 data")


@dataclass
class OECD(Data):
    """An object to download and return the latest OECD DAC deflators data."""

    def __post_init__(self):
        self._available_methods = {"dac_deflator": "oecd_dac"}

    def update(self, **kwargs) -> None:
        _update_dac1()

    def load_data(self, **kwargs) -> None:
        try:
            self._data = pd.read_feather(PYDEFLATE_PATHS.data / "dac1.feather")
        except FileNotFoundError:
            logger.info("Data not found, downloading...")
            self.update()
        finally:
            self._data = (
                pd.read_feather(PYDEFLATE_PATHS.data / "dac1.feather")
                .assign(indicator="oecd_dac")
                .rename(columns={"deflator": "value"})
            )
