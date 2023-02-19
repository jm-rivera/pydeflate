from dataclasses import dataclass

import pandas as pd
from bblocks import WorldEconomicOutlook, set_bblocks_data_path

from pydeflate.get_data.deflate_data import Data
from pydeflate.pydeflate_config import PYDEFLATE_PATHS
from pydeflate.tools.update_data import update_update_date

set_bblocks_data_path(PYDEFLATE_PATHS.data)


@dataclass
class IMF(Data):
    _weo: WorldEconomicOutlook = None
    """An object to download and return the latest IMF WEO data for several indicators"""

    def __post_init__(self):
        self._weo = WorldEconomicOutlook()
        self._available_methods = {
            "Consumer price index": "PCPI",
            "Consumer price index, end of period": "PCPIE",
            "Gross domestic product, deflator": "NGDP_D",
            "gdp": "NGDP_D",
            "pcpi": "PCPI",
            "pcpie": "PCPIE",
        }

    def update(self) -> None:
        """Update the stored WEO data, using WEO package."""
        self._weo.update_data(reload_data=False, year=None, release=None)
        update_update_date(source="IMF")

    def load_data(
        self, latest_y: int | None = None, latest_r: int | None = None
    ) -> None:
        """Loading WEO as a clean dataframe

        Args:
            latest_y: passed only optional to override the behaviour to get the latest
            release year for the WEO.
            latest_r: passed only optionally to override the behaviour to get the latest
            released value (1 or 2).
        """
        # load the data for available indicators
        indicators = list(self._available_methods.values()) + ["NGDP", "NGDPD"]
        self._weo.load_data(indicators)

        # get the data into a dataframe
        self._data = self._weo.get_data(keep_metadata=False)

    def implied_exchange(self, direction: str = "lcu_usd") -> pd.DataFrame:
        """Get the implied exchange rate used by the IMF
        Args:
            direction: the direction of the exchange rate, either lcu_usd for
            local currency units per usd, or usd_lcu for the opposite.
        """

        # USD data
        usd = self.get_method("NGDPD")

        # LCU data
        lcu = self.get_method("NGDP")

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
