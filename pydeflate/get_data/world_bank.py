from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from pydeflate.core.classes import Data
from pydeflate.core.dtypes import set_default_types
from pydeflate.core.schema import PydeflateSchema
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger

from bblocks import WorldBankData, set_bblocks_data_path

from pydeflate.tools.common import year_to_int, add_exchange_deflator
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


def update_world_bank_data(force_update: bool = False) -> None:
    """Update World Bank data."""
    logger.info("Downloading World Bank data... this may take a while.")
    wb = WorldBankData().load_data(
        indicator=list(_INDICATORS.values()), start_year=START, end_year=END
    )
    if force_update:
        wb.update_data()
    update_update_date(source="World Bank")
    logger.info("World Bank data updated.")


def read_wb_file(path):
    return pd.read_csv(path, parse_dates=["date"]).rename(columns={"date": "year"})


@dataclass
class WorldBank(Data):
    """An object to download and return the latest WorldBank exchange and price data"""

    _exchange: dict[str, pd.DataFrame] = field(default_factory=dict)
    _data: dict[str, pd.DataFrame] = field(default_factory=dict)
    _paths: dict[str, Path] = field(default_factory=dict)

    def get_data(self, **kwargs) -> pd.DataFrame:
        pass

    def _get_data_paths(self) -> "WorldBank":
        # get the paths to the data
        self._paths = {
            i_: PYDEFLATE_PATHS.data / f"{_INDICATORS[i_]}_{START}-{END}_.csv"
            for i_ in _INDICATORS
        }
        return self

    def __post_init__(self):
        self._available_methods = {
            "gdp": "GDP deflator",
            "gdp_linked": "GDP deflator linked",
            "cpi": "Consumer price index",
        }

        # load data paths
        self._get_data_paths()

    def update(self, **kwargs) -> "WorldBank":
        """Update data for all WorldBank indicators"""
        update_world_bank_data()
        return self

    def _check_if_data_exists(self):
        for path in self._paths.values():
            if not path.exists():
                update_world_bank_data(force_update=False)
                break

    @staticmethod
    def _process_exchange(data) -> pd.DataFrame:
        data = (
            data.pipe(year_to_int)
            .rename(
                columns={
                    "value": PydeflateSchema.EXCHANGE,
                    "indicator_code": PydeflateSchema.INDICATOR,
                }
            )
            .pipe(set_default_types)
            .pipe(add_exchange_deflator)
        )

        return data

    def load_data(self) -> None:
        """Load data for all WorldBank indicators"""

        # Load exchange rates
        for method in ["exchange", "effective_exchange"]:
            self._exchange[method] = read_wb_file(self._paths[method]).pipe(
                self._process_exchange
            )

        # for path in self._paths:
        #     try:
        #         d_ = pd.read_csv(path, parse_dates=["date"]).rename(
        #             columns={"date": "year"}
        #         )
        #         self._data[path.name.split("/")[-1].split("_")[0]] = d_
        #
        #     except FileNotFoundError:
        #         pass


if __name__ == "__main__":
    wb = WorldBank()
    wb.load_data()
