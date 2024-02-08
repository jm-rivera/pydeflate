import warnings
from dataclasses import dataclass

import pandas as pd

from pydeflate.core.schema import PydeflateSchema
from pydeflate.get_data.deflators.deflate_data import Data
from pydeflate.get_data.exchange.exchange_data import ExchangeOECD
from pydeflate.get_data.oecd_tools import (
    read_zip_content,
    download_bulk_file,
    clean_dac1,
    identify_base_year,
)
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.tools.update_data import update_update_date

warnings.simplefilter("ignore", Warning, lineno=1013)


_BASE_URL: str = "https://stats.oecd.org/DownloadFiles.aspx?DatasetCode="
_TABLE1_URL: str = f"{_BASE_URL}TABLE1"
FILE_NAME: str = "dac1"


def update_dac1() -> None:
    """Update dac1 data from OECD site and save as feather"""

    logger.info("Downloading DAC1 data, which may take a bit")

    # File name to read
    file_name = "Table1_Data.csv"

    # Download the zip bytes
    zip_bytes = download_bulk_file(url=_TABLE1_URL)

    # Read the zip file and clean the data
    df = (
        read_zip_content(request_content=zip_bytes, file_name=file_name)
        .pipe(clean_dac1)
        .reset_index(drop=True)
    )

    # Save the data
    df.to_feather(PYDEFLATE_PATHS.data / "dac1.feather")

    # Update the update date
    update_update_date("OECD DAC")

    # Log
    logger.info("Successfully downloaded DAC1 data")


def calculate_price_deflator(deflators_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate what the price deflator should be, based on the deflator and exchange
    information."""
    deflators_df[PydeflateSchema.VALUE] = round(
        deflators_df[f"{PydeflateSchema.VALUE}_dac"]
        * deflators_df[f"{PydeflateSchema.VALUE}_exchange"]
        / 100,
        6,
    )

    return deflators_df.filter(
        [
            PydeflateSchema.ISO_CODE,
            PydeflateSchema.YEAR,
            PydeflateSchema.INDICATOR,
            PydeflateSchema.VALUE,
        ],
        axis=1,
    )


@dataclass
class OECD(Data):
    """An object to download and return the latest OECD DAC deflators data."""

    _tries: int = 0
    _file: pd.DataFrame | None = None

    def __post_init__(self):
        self._available_methods = {"dac_deflator": "oecd_dac"}

    def update(self, **kwargs) -> None:
        update_dac1()

    def _load(self) -> None:
        """Tries to load file (and attempts two downloads otherwise)"""
        self._tries += 1
        try:
            # Try loading the file and renaming the deflator column "value"
            self._file = pd.read_feather(
                PYDEFLATE_PATHS.data / f"{FILE_NAME}.feather"
            ).rename(columns={PydeflateSchema.DEFLATOR: PydeflateSchema.VALUE})
        except FileNotFoundError:
            logger.info("Data not found, downloading...")
            self.update()
            if self._tries < 3:
                self._load()
            else:
                raise FileNotFoundError("Data could not be downloaded")

    def load_data(self, **kwargs) -> None:
        """Load the OECD DAC price deflators data.

        If the data is not found, it will be downloaded.
        DAC deflators are transformed into price deflators by using the
        implied exchange rate information from the OECD DAC data.

        The deflators that are loaded is therefore *not* the DAC deflator,
        but the price deflator used to produce the DAC deflators.

        """
        self._load()

        df = self._file

        # Identify base year
        base_year = identify_base_year(df=df)

        # Load exchange deflators
        exchange_deflator = ExchangeOECD().exchange_deflator(
            source_iso="USA", target_iso="USA", base_year=base_year
        )

        # Merge deflators and exchange deflators
        deflators_df = df.merge(
            exchange_deflator,
            on=[PydeflateSchema.ISO_CODE, PydeflateSchema.YEAR],
            how="left",
            suffixes=("_dac", "_exchange"),
        )

        # Calculate the price deflator
        self._data = calculate_price_deflator(deflators_df=deflators_df)
