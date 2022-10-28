from dataclasses import dataclass
from typing import Union, Callable

import pandas as pd
from weo import WEO, all_releases, download

from pydeflate import utils
from pydeflate.config import PYDEFLATE_PATHS
from pydeflate.get_data.data import Data


def _check_weo_parameters(
    latest_y: Union[int, None] = None, latest_r: Union[int, None] = None
) -> (int, int):
    """Check parameters and return max values or provided input"""
    if latest_y is None:
        latest_y = max(*all_releases())[0]

    # if latest release isn't provided, take max value
    if latest_r is None:
        latest_r = max(*all_releases())[1]

    return latest_y, latest_r


def _update_weo(latest_y: int = None, latest_r: int = None) -> None:
    """Update data from the World Economic Outlook, using WEO package"""

    latest_y, latest_r = _check_weo_parameters(latest_y, latest_r)

    # Download the file from the IMF website and store in directory
    download(
        latest_y,
        latest_r,
        directory=PYDEFLATE_PATHS.data,
        filename=f"weo{latest_y}_{latest_r}.csv",
    )
    utils.update_update_date("imf")


@dataclass
class IMF(Data):
    method: Union[str, None] = None
    data: pd.DataFrame = None
    """An object to download and return the latest IMF WEO data for several indicators"""

    def update(
        self, latest_y: Union[int, None] = None, latest_r: Union[int, None] = None
    ) -> None:
        """Update the stored WEO data, using WEO package.

        Args:
            latest_y: passed only optional to override the behaviour to get the latest
            release year for the WEO.
            latest_r: passed only optionally to override the behaviour to get the latest
            released value (1 or 2).
        """
        _update_weo(latest_y=latest_y, latest_r=latest_r)

    def load_data(
        self, latest_y: Union[int, None] = None, latest_r: Union[int, None] = None
    ) -> None:
        """loading WEO as a clean dataframe

        Args:
            latest_y: passed only optional to override the behaviour to get the latest
            release year for the WEO.
            latest_r: passed only optionally to override the behaviour to get the latest
            released value (1 or 2).
        """

        latest_y, latest_r = _check_weo_parameters(latest_y, latest_r)

        names = {
            "ISO": "iso_code",
            "WEO Subject Code": "indicator",
            "Subject Descriptor": "indicator_name",
            "Units": "units",
            "Scale": "scale",
        }
        to_drop = [
            "WEO Country Code",
            "Country",
            "Subject Notes",
            "Country/Series-specific Notes",
            "Estimates Start After",
        ]

        df = WEO(PYDEFLATE_PATHS.data / f"weo{latest_y}_{latest_r}.csv").df

        self.data = (
            df.drop(to_drop, axis=1)
            .rename(columns=names)
            .melt(id_vars=names.values(), var_name="date", value_name="value")
            .assign(
                year=lambda d: pd.to_datetime(d.date, format="%Y"),
                value=lambda d: d.value.apply(utils.clean_number),
            )
            .dropna(subset=["value"])
            .drop("date", axis=1)
            .reset_index(drop=True)
        )

    def _get_indicator(self, indicator: str) -> pd.DataFrame:
        """Get a specified imf indicator from the downloaded WEO file"""

        return (
            self.data.loc[lambda d: d.indicator == indicator]
            .filter(["iso_code", "year", "value"], axis=1)
            .sort_values(["iso_code", "year"])
            .reset_index(drop=True)
        )

    def inflation_acp(self) -> pd.DataFrame:
        """Indicator PCPI, Index"""
        return self._get_indicator("PCPI")

    def inflation_epcp(self) -> pd.DataFrame:
        """Indicator PCPIE, Index"""
        return self._get_indicator("PCPIE")

    def inflation_gdp(self) -> pd.DataFrame:
        return self._get_indicator("NGDP_D")

    def available_methods(self) -> dict[str, Callable]:
        return {
            "gdp": self.inflation_gdp,
            "pcpi": self.inflation_acp,
            "pcpie": self.inflation_epcp,
        }

    def get_data(self, **kwargs):
        pass

    def get_deflator(self, **kwargs) -> pd.DataFrame:
        """Get the deflator DataFrame for the specified method"""

        self._check_method()

        if self.data is None:
            self.load_data()

        return self.available_methods()[self.method]()
