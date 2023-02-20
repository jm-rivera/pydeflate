from dataclasses import dataclass

import pandas as pd
from pydeflate.get_data.deflate_data import Data
from pydeflate.pydeflate_config import PYDEFLATE_PATHS

from bblocks import WorldBankData, set_bblocks_data_path

from pydeflate.tools.update_data import update_update_date

set_bblocks_data_path(PYDEFLATE_PATHS.data)

_INDICATORS: dict = {
    "gdp": "NY.GDP.DEFL.ZS",
    "gdp_linked": "NY.GDP.DEFL.ZS.AD",
    "cpi": "FP.CPI.TOTL",
    "exchange": "PA.NUS.FCRF",
    "effective_exchange": "PX.REX.REER",
}

START: int = 1950
END: int = 2025


def update_world_bank_data() -> None:
    """Update World Bank data."""
    wb = WorldBankData()
    wb.load_data(indicator=list(_INDICATORS.values()), start_year=START, end_year=END)
    wb.update_data()
    update_update_date(source="World Bank")


@dataclass
class WorldBank(Data):
    """An object to download and return the latest WorldBank exchange and price data"""

    def __post_init__(self):
        self._available_methods = {
            "gdp": "GDP deflator",
            "gdp_linked": "GDP deflator linked",
            "cpi": "Consumer price index",
        }

    def update(self, **kwargs) -> None:
        """Update data for all WorldBank indicators"""
        update_world_bank_data()

    def load_data(self) -> None:
        """Load data for all WorldBank indicators"""

        # get the paths to the data
        paths = [
            PYDEFLATE_PATHS.data / f"{_INDICATORS[i_]}_{START}-{END}_.csv"
            for i_ in _INDICATORS
        ]

        # check if data exists, if not update
        for path in paths:
            if not path.exists():
                update_world_bank_data()
                break

        # load the data
        files = []
        for path in paths:
            try:
                files.append(
                    pd.read_csv(path, parse_dates=["date"]).rename(
                        columns={"date": "year"}
                    )
                )
            except FileNotFoundError:
                files.append(pd.DataFrame())

        self._data = pd.concat(files, ignore_index=True)
