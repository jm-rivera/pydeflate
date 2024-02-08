from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from bblocks import WorldEconomicOutlook, set_bblocks_data_path

from pydeflate.core.classes import Data
from pydeflate.core.dtypes import set_default_types
from pydeflate.core.schema import PydeflateSchema
from pydeflate.get_data.oecd_tools import add_exchange
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, DEFAULT_BASE
from pydeflate.tools.common import rebase, year_to_int, add_exchange_deflator
from pydeflate.tools.update_data import update_update_date

set_bblocks_data_path(PYDEFLATE_PATHS.data)


@dataclass
class IMF(Data):
    _weo: WorldEconomicOutlook = None

    """An object to download and return the latest IMF WEO data for several indicators"""

    def __post_init__(self):
        # Load the WEO object
        self._weo = WorldEconomicOutlook()

        # Load the available methods data
        self._available_methods = {
            "Consumer price index": "PCPI",
            "Consumer price index, end of period": "PCPIE",
            "Gross domestic product, deflator": "NGDP_D",
            "gdp": "NGDP_D",
            "pcpi": "PCPI",
            "pcpie": "PCPIE",
        }

        # Set .data as an empty dictionary
        self.data = {}

    def _price_deflator(self, method: str) -> pd.DataFrame:
        """Add the price deflator to the data"""

        # Pipeline for a method
        data = (
            self._weo.get_data(indicators=method, keep_metadata=False)
            .rename(columns={"value": PydeflateSchema.PRICE_DEFLATOR})
            .pipe(year_to_int)
            .pipe(
                rebase,
                new_base_year=DEFAULT_BASE,
                deflator_column=PydeflateSchema.PRICE_DEFLATOR,
            )
            .pipe(set_default_types)
        )

        return data

    def _implied_exchange(self) -> pd.DataFrame:
        """Get the implied exchange rate used by the IMF"""

        # USD data
        usd = self._weo.get_data("NGDPD")

        # LCU data
        lcu = self._weo.get_data("NGDP")

        # Merge datasets
        d_ = usd.merge(lcu, on=["iso_code", "year"], suffixes=("_usd", "_lcu")).pipe(
            year_to_int
        )

        # Add exchange rate
        d_ = add_exchange(d_, lcu="value_lcu", current_usd="value_usd")

        # Add exchange rate deflator
        d_ = add_exchange_deflator(d_)

        return d_.filter(
            [
                PydeflateSchema.ISO_CODE,
                PydeflateSchema.YEAR,
                PydeflateSchema.EXCHANGE,
                PydeflateSchema.EXCHANGE_DEFLATOR,
            ]
        ).pipe(set_default_types)

    def update(self) -> "IMF":
        """Update the stored WEO data, using WEO package."""
        self._weo.update_data(reload_data=True, year=None, release=None)
        update_update_date(source="IMF")
        return self

    def load_data(
        self, latest_y: int | None = None, latest_r: int | None = None
    ) -> "IMF":
        """Loading WEO as a clean dataframe

        Args:
            latest_y: passed only optional to override the behaviour to get the latest
            release year for the WEO.
            latest_r: passed only optionally to override the behaviour to get the latest
            released value (1 or 2).
        """
        # load the data for available indicators
        indicators = list(set(self._available_methods.values())) + ["NGDP", "NGDPD"]
        self._weo.load_data(indicators)

        # Load exchange data
        self._exchange["imf_weo"] = self._implied_exchange()

        # get the data into a dataframe
        for method in set(self._available_methods.values()):
            self._data[method] = self._price_deflator(method=method)

        return self

    def get_data(
        self, deflator_method: str = "gdp", exchange_method: str = "imf_weo", **kwargs
    ) -> pd.DataFrame:
        # Combine the price and exchange

        self.data[deflator_method] = self._data[
            self._available_methods[deflator_method]
        ].merge(
            self._exchange[exchange_method],
            on=[PydeflateSchema.ISO_CODE, PydeflateSchema.YEAR],
            how="left",
        )
        return self.data[deflator_method]


if __name__ == "__main__":
    imf = IMF().load_data()
    df = imf.get_data()
