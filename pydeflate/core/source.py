from dataclasses import dataclass, field

import pandas as pd

from pydeflate.sources.common import AvailableDeflators
from pydeflate.sources.dac import read_dac
from pydeflate.sources.imf import read_weo
from pydeflate.sources.world_bank import read_wb, read_wb_lcu_ppp, read_wb_usd_ppp


@dataclass
class Source:
    name: str
    reader: callable
    update: bool = False
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    _idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

    def __post_init__(self):
        self.data = self.reader(self.update)
        self.validate()

    def validate(self):
        if self.data.empty:
            raise ValueError(f"No data found for {self.name}")

        # check all columns start with pydeflate_
        if not all(col.startswith("pydeflate_") for col in self.data.columns):
            raise ValueError(f"Invalid data format for {self.name}")

    def lcu_usd_exchange(self) -> pd.DataFrame:
        return self.data.filter(self._idx + ["pydeflate_EXCHANGE"])

    def price_deflator(self, kind: AvailableDeflators = "NGDP_D") -> pd.DataFrame:

        if f"pydeflate_{kind}" not in self.data.columns:
            raise ValueError(f"No deflator data found for {kind} in {self.name} data.")

        return self.data.filter(self._idx + [f"pydeflate_{kind}"])


class IMF(Source):
    def __init__(self, update: bool = False):
        super().__init__(name="IMF", reader=read_weo, update=update)


class WorldBank(Source):
    def __init__(self, update: bool = False):
        super().__init__(name="World Bank", reader=read_wb, update=update)


class WorldBankPPP(Source):
    def __init__(self, update: bool = False, *, from_lcu: bool = True):
        super().__init__(
            name="World Bank PPP",
            reader=read_wb_lcu_ppp if from_lcu else read_wb_usd_ppp,
            update=update,
        )


class DAC(Source):
    def __init__(self, update: bool = False):
        super().__init__(name="DAC", reader=read_dac, update=update)
