import warnings

import pandas as pd

from pydeflate.core.classes import Data
from pydeflate.core.schema import PydeflateSchema
from pydeflate.get_data.oecd_tools import (
    read_zip_content,
    download_bulk_file,
    clean_dac1,
)
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger, DEFAULT_BASE
from pydeflate.tools.common import rebase
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


class OECD_DAC(Data):
    """An object to download and return the latest OECD DAC deflators data."""

    def update(self, **kwargs) -> "OECD_DAC":
        update_dac1()
        return self

    def load_data(self) -> "OECD_DAC":
        """Tries to load file (and attempts two downloads otherwise)"""
        self._tries += 1
        try:
            # Try loading the file and renaming the deflator column "value"
            self.data = pd.read_feather(PYDEFLATE_PATHS.data / f"{FILE_NAME}.feather")

        except FileNotFoundError:
            logger.info("Data not found, downloading...")
            self.update()
            if self._tries < 3:
                self.load_data()
            else:
                raise FileNotFoundError("Data could not be downloaded")

        for deflator in [
            PydeflateSchema.EXCHANGE_DEFLATOR,
            PydeflateSchema.PRICE_DEFLATOR,
        ]:
            data = rebase(
                self.data, new_base_year=DEFAULT_BASE, deflator_column=deflator
            )

        self.data = {"oecd_dac": data}
        return self

    def get_data(self, method: str = "oecd_dac", **kwargs) -> pd.DataFrame:
        return self.data[method]


if __name__ == "__main__":
    oda = OECD_DAC()

    df = oda.load_data().get_data()
