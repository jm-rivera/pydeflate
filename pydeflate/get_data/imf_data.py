from dataclasses import dataclass
from bblocks import set_bblocks_data_path, WorldEconomicOutlook

import pandas as pd

from pydeflate.pydeflate_config import PYDEFLATE_PATHS
from pydeflate.get_data.data import Data

set_bblocks_data_path(PYDEFLATE_PATHS.data)


@dataclass
class IMF(Data):
    method: str | None = None
    data: pd.DataFrame = None
    _weo: WorldEconomicOutlook = None
    """An object to download and return the latest IMF WEO data for several indicators"""

    def __post_init__(self):
        self._weo = WorldEconomicOutlook()

    def update(self) -> None:
        """Update the stored WEO data, using WEO package."""
        self._weo.update_data(reload_data=False)

    def load_data(
        self, latest_y: int | None = None, latest_r: int | None = None
    ) -> None:
        """loading WEO as a clean dataframe

        Args:
            latest_y: passed only optional to override the behaviour to get the latest
            release year for the WEO.
            latest_r: passed only optionally to override the behaviour to get the latest
            released value (1 or 2).
        """
        # load the data for available indicators
        indicators = ["PCPI", "PCPIE", "NGDP_D", "NGDP", "NGDPD"]
        self._weo.load_data(indicators)

        # get the data into a dataframe
        self.data = self._weo.get_data(keep_metadata=False)

    def _get_indicator(self, indicator: str) -> pd.DataFrame:
        """Get a specified imf indicator from the downloaded WEO file"""
        if self.data is None:
            self.load_data()
        return (
            self.data.loc[lambda d: d.indicator == indicator]
            .filter(["iso_code", "year", "value"], axis=1)
            .sort_values(["iso_code", "year"])
            .reset_index(drop=True)
        )

    def implied_exchange(self, direction: str = "lcu_usd") -> pd.DataFrame:
        """Get the implied exchange rate used by the IMF
        Args:
            direction: the direction of the exchange rate, either lcu_usd for
            local currency units per usd, or usd_lcu for the opposite
        """

        # USD data
        usd = self._get_indicator("NGDPD")

        # LCU data
        lcu = self._get_indicator("NGDP")

        # Merge datasets
        d_ = usd.merge(lcu, on=["iso_code", "year"], suffixes=("_usd", "_lcu"))

        # Calculate implied exchange rate
        if direction == "lcu_usd":
            d_["value"] = d_["value_lcu"] / d_["value_usd"]
        elif direction == "usd_lcu":
            d_["value"] = d_["value_usd"] / d_["value_lcu"]
        else:
            raise ValueError(f"direction must be lcu_usd or usd_lcu, not {direction}")

        return d_.filter(["iso_code", "year", "value"], axis=1)

    def inflation_acp(self) -> pd.DataFrame:
        """Indicator PCPI, Index"""
        return self._get_indicator("PCPI")

    def inflation_epcp(self) -> pd.DataFrame:
        """Indicator PCPIE, Index"""
        return self._get_indicator("PCPIE")

    def inflation_gdp(self) -> pd.DataFrame:
        return self._get_indicator("NGDP_D")

    def available_methods(self) -> dict[str, callable]:
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
