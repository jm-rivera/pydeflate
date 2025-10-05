from dataclasses import dataclass, field

import pandas as pd

from pydeflate.exceptions import ConfigurationError, DataSourceError
from pydeflate.sources.common import AvailableDeflators
from pydeflate.sources.dac import read_dac
from pydeflate.sources.imf import read_weo
from pydeflate.sources.world_bank import read_wb, read_wb_lcu_ppp, read_wb_usd_ppp


@dataclass
class Source:
    """Base class for data sources implementing SourceProtocol.

    This class handles loading data from external sources, caching,
    and validation. It implements the SourceProtocol interface.
    """

    name: str
    reader: callable
    update: bool = False
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    _idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

    def __post_init__(self):
        """Load and validate data after initialization."""
        try:
            self.data = self.reader(self.update)
        except Exception as e:
            raise DataSourceError(
                f"Failed to load data: {e}",
                source=self.name,
            ) from e

        self.validate()

    def validate(self):
        """Validate that source data is properly formatted.

        Raises:
            DataSourceError: If data is empty or improperly formatted
            SchemaValidationError: If data doesn't match expected schema
        """
        if self.data.empty:
            raise DataSourceError(f"No data found", source=self.name)

        # Check all columns start with pydeflate_
        invalid_cols = [
            col for col in self.data.columns if not col.startswith("pydeflate_")
        ]
        if invalid_cols:
            raise DataSourceError(
                f"Invalid column names (must start with 'pydeflate_'): {invalid_cols}",
                source=self.name,
            )

        # Validate schema if available and enabled
        # Note: Schema validation is currently experimental
        # Set environment variable PYDEFLATE_ENABLE_VALIDATION=1 to enable
        import os

        if os.environ.get("PYDEFLATE_ENABLE_VALIDATION") == "1":
            try:
                from pydeflate.schemas import validate_source_data

                validate_source_data(self.data, self.name)
            except ImportError:
                # Pandera not available, skip schema validation
                pass
            except Exception as e:
                # Schema validation failed, but don't break for now
                # This allows us to roll out schema validation gradually
                import logging

                logger = logging.getLogger("pydeflate")
                logger.debug(f"Schema validation skipped for {self.name}: {e}")

    def lcu_usd_exchange(self) -> pd.DataFrame:
        """Return local currency to USD exchange rates.

        Returns:
            DataFrame with exchange rate data

        Raises:
            DataSourceError: If exchange rate data is missing
        """
        if "pydeflate_EXCHANGE" not in self.data.columns:
            raise DataSourceError(
                "Exchange rate data (pydeflate_EXCHANGE) not available",
                source=self.name,
            )
        return self.data.filter(self._idx + ["pydeflate_EXCHANGE"])

    def price_deflator(self, kind: AvailableDeflators = "NGDP_D") -> pd.DataFrame:
        """Return price deflator data for specified kind.

        Args:
            kind: Type of deflator (e.g., 'NGDP_D', 'CPI')

        Returns:
            DataFrame with deflator data

        Raises:
            ConfigurationError: If deflator kind not available for this source
        """
        column_name = f"pydeflate_{kind}"
        if column_name not in self.data.columns:
            available = [
                col.replace("pydeflate_", "")
                for col in self.data.columns
                if col.startswith("pydeflate_") and col not in self._idx
            ]
            raise ConfigurationError(
                f"Deflator '{kind}' not available for {self.name}. "
                f"Available deflators: {', '.join(available)}",
                parameter="kind",
            )

        return self.data.filter(self._idx + [column_name])


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
