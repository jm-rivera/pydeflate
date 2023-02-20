from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from pydeflate.get_data.imf_data import IMF
from pydeflate.get_data.wb_data import END, START, update_world_bank_data
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.utils import emu


def _exchange_ratio(source_xe: pd.DataFrame, target_xe: pd.DataFrame) -> pd.DataFrame:
    return (
        source_xe.merge(
            target_xe,
            how="left",
            on=["year", "iso_code"],
            suffixes=("_source", "_target"),
        )
        .assign(value=lambda d: d.value_source / d.value_target)
        .drop(["value_source", "value_target"], axis=1)
    )


def _calculate_deflator(xe: pd.DataFrame, base_year: int) -> pd.DataFrame:
    # get the data for the selected base year.
    xe_base = xe.query(f"year.dt.year == {base_year}")

    # If base year is not valid, raise error
    if len(xe_base) == 0:
        raise ValueError(f"No currency exchange data for {base_year=}")

    # Merge the exchange data and the base year data
    xe = xe.merge(xe_base, how="left", on=["iso_code"], suffixes=("", "_base"))

    # Calculate the deflator
    xe.value = round(100 * xe.value / xe.value_base, 6)

    return xe.filter(["iso_code", "year", "value"], axis=1)


@dataclass
class Exchange(ABC):
    """An abstract class to update, load and return exchange rate data.

    Attributes:
        method: the method to use to calculate the exchange rate.

    """

    method: str | None
    _data: pd.DataFrame | None = None

    @abstractmethod
    def update(self, **kwargs) -> None:
        """Update underlying data"""

    @abstractmethod
    def load_data(self, **kwargs) -> None:
        """Load required data to construct deflator"""

    @abstractmethod
    def usd_exchange_rate(self, direction: str = "lcu_to_uds") -> pd.DataFrame:
        """Get the exchange rate of a currency to USD (or vice versa)

        Args:
            direction: the direction of the exchange rate. Either "lcu_to_usd"
            or "usd_to_lcu".

        Returns:
            A dataframe with the exchange rate of the currency to USD (or vice versa).
        """

    def exchange_rate(self, currency_iso: str) -> pd.DataFrame:
        """Get an exchange rate for a given ISO

        Args:
            currency_iso: the iso_code of the currency to get the exchange rate for.

        Returns:
            A dataframe with the exchange rate for the specified currency.
        """

        # get usd exchange rates
        d_ = self.usd_exchange_rate()

        # filter the exchange rate of the chosen currency
        target_iso = d_.query(f"iso_code == '{currency_iso}'")

        # If currency is not valid, raise error
        if len(target_iso) == 0:
            raise ValueError(f"No currency exchange data for {currency_iso=}")

        # merge the two datasets and calculate new exchange rate
        return (
            pd.merge(d_, target_iso, how="left", on=["year"], suffixes=("", "_xe"))
            .assign(value=lambda d: d.value / d.value_xe)
            .drop(columns=["value_xe", "iso_code_xe"])
        )

    def exchange_deflator(
        self, source_iso: str, target_iso: str, base_year: int
    ) -> pd.DataFrame:
        """Get an exchange rate deflator for a given ISO

        Args:
            source_iso: the iso_code in which the "original" data is based.
                The default should be "LCU".
            target_iso: the iso_code of the currency to get the exchange rate for.
            base_year: the base year to calculate the deflator.

        Returns:
            A dataframe with the exchange rate deflator for the specified currency.

        """
        # Get exchange data based on the source currency. If LCU set to None
        source_xe = (
            self.exchange_rate(currency_iso=source_iso)
            if source_iso != "LCU"
            else self.exchange_rate(currency_iso="USA").assign(value=1)
        )

        # Get exchange data based on the target currency. If LCU set to None
        target_xe = (
            self.exchange_rate(currency_iso=target_iso)
            if target_iso != "LCU"
            else self.exchange_rate(currency_iso="USA").assign(value=1)
        )

        # calculate conversion ratio
        exchange_ratio = _exchange_ratio(source_xe=source_xe, target_xe=target_xe)

        # get the data for the selected base year.
        if target_iso != "LCU":
            xe = self.exchange_rate(currency_iso=target_iso)
        elif source_iso != "LCU":
            xe = self.exchange_rate(currency_iso=source_iso)
        else:
            xe = self.exchange_rate(currency_iso="USA").assign(value=1)

        # Calculate the deflator
        xe = _calculate_deflator(xe=xe, base_year=base_year)

        # Merge the conversion ratio
        xe = xe.merge(
            exchange_ratio,
            how="left",
            on=["year", "iso_code"],
            suffixes=("_xe", "_xe_ratio"),
        )

        # Convert deflators to currency of interest
        xe = xe.assign(value=lambda d: d.value_xe * d.value_xe_ratio)

        return xe.filter(["year", "iso_code", "value"], axis=1)


@dataclass
class ExchangeOECD(Exchange):
    """The OECD exchange rate data

    Attributes:
        method: the method to use to calculate the exchange rate. For this source,
        the only valid method is “implied”.
    """

    method: str = "implied"
    _load_try_count: int = 0

    @staticmethod
    def update(**kwargs) -> None:
        """Update the DAC1 data, which is the source for the OECD exchange rates."""
        from pydeflate.get_data import oecd_data

        oecd_data.update_dac1()

    def load_data(self, **kwargs) -> None:
        """Load the DAC1 data, which is the source for the OECD exchange rates."""
        # avoid infinite recursion
        if self._load_try_count < 1:
            try:
                self._data = pd.read_feather(PYDEFLATE_PATHS.data / "dac1.feather")
            except FileNotFoundError:
                logger.info("OECD Data not found, downloading...")
                self._load_try_count = +1
                self.update()
                self.load_data()
        else:
            raise FileNotFoundError("Could not load OECD data")

    def usd_exchange_rate(self, direction: str = "lcu_usd") -> pd.DataFrame:
        """Get the exchange rate of a currency to USD (or vice versa)

        Args:
            direction: the direction of the exchange rate. Either "lcu_to_usd"
            or "usd_to_lcu".

        Returns:
            A dataframe with the exchange rate of the currency to USD (or vice versa).
        """

        # If data is not loaded, load it
        if self._data is None:
            self.load_data()

        # Filter the data to only include the required columns, rename the value column.
        d_ = self._data[["iso_code", "year", "exchange"]].rename(
            columns={"exchange": "value"}
        )

        # if the direction is lcu to usd, return the data
        if direction == "lcu_usd":
            return d_
        # if the direction is usd to lcu, invert the exchange rate.
        elif direction == "usd_lcu":
            d_.value = 1 / d_.value
            return d_
        # if the direction is not valid, raise error
        else:
            raise ValueError("Direction must be 'lcu_usd' or 'usd_lcu'")


@dataclass
class ExchangeWorldBank(Exchange):
    """The World Bank exchange rate data

    Attributes:
        method: the method to use to calculate the exchange rate. For this source,
        the valid methods are "yearly_average" and "effective_exchange".
    """

    method: str = "yearly_average"
    _load_try_count: int = 0

    def __post_init__(self):
        """Check that the method is valid"""
        if self.method not in ["yearly_average", "effective_exchange"]:
            raise ValueError("Method must be 'yearly_average' or 'effective_exchange'")

    def update(self) -> None:
        """Update the World Bank data"""
        update_world_bank_data()

    def load_data(self, **kwargs) -> None:
        """Load the World Bank data"""
        # method mapping
        method_map = {
            "yearly_average": "PA.NUS.FCRF",
            "effective_exchange": "PX.REX.REER",
        }

        if self._load_try_count < 1:
            # Try to load the data from disk
            try:
                self._data = (
                    pd.read_csv(
                        PYDEFLATE_PATHS.data
                        / f"{method_map[self.method]}_{START}-{END}_.csv",
                        parse_dates=["date"],
                    )
                    .rename(columns={"date": "year"})
                    .drop(columns=["indicator_code"])
                )

            # If the data is not found, download it. Reload the data to the object.
            except FileNotFoundError:
                logger.info("World Bank data not found, downloading...")
                self._load_try_count = +1
                self.update()
                self.load_data()
        else:
            raise FileNotFoundError("Could not load World Bank data")

    def usd_exchange_rate(self, direction: str = "lcu_usd") -> pd.DataFrame:
        """Get the exchange rate of a currency to USD (or vice versa)

        Args:
            direction: the direction of the exchange rate. Either "lcu_to_usd"
            or "usd_to_lcu".

        Returns:
            A dataframe with the exchange rate of the currency to USD (or vice versa).

        """

        if direction not in ["lcu_usd", "usd_lcu"]:
            raise ValueError("Direction must be 'lcu_usd' or 'usd_lcu'")

        # If data is not loaded, load it
        if self._data is None:
            self.load_data()

        # Load the data into a temporary variable
        df = self._data.copy(deep=True)

        # Find the "Euro" data. This is done given that some countries are missing
        # exchange rates, but they are part of the Euro area.
        eur = df.loc[df.iso_code == "EMU"].dropna().set_index("year")["value"].to_dict()

        # Euro area countries without exchange rates
        eur_mask = (df.iso_code.isin(emu())) & (df.value.isna())

        # Assign EURO exchange rate to euro are countries from year euro adopted
        df.loc[eur_mask, "value"] = df.year.map(eur)

        # If the direction is lcu to usd, return the data

        if direction == "lcu_usd":
            return df
        # if the direction is usd to lcu, invert the exchange rate.

        df.value = 1 / df.value
        return df


@dataclass
class ExchangeIMF(Exchange):
    """The IMF exchange rate data

    Attributes:
        method: the method to use to calculate the exchange rate. For this source,
        the only valid method is “implied”.

    """

    method: str = "implied"
    _imf: IMF | None = None

    def __post_init__(self):
        """Load an IMF object to manage getting the data"""
        if self._imf is None:
            self._imf = IMF()

    def update(self, **kwargs) -> None:
        """Update the IMF data"""
        self._imf.update()

    def load_data(self, **kwargs) -> None:
        """Load the IMF data"""

        # if no direction is passed, default to lcu to usd
        direction = "lcu_usd" if "direction" not in kwargs else kwargs["direction"]
        self._data = self._imf.implied_exchange(direction=direction)

    def usd_exchange_rate(self, direction: str = "lcu_usd") -> pd.DataFrame:
        """Get the exchange rate of a currency to USD (or vice versa)

        Args:
            direction: the direction of the exchange rate. Either "lcu_to_usd"
            or "usd_to_lcu".

        Returns:
            A dataframe with the exchange rate of the currency to USD (or vice versa).

        """

        if direction not in ["lcu_usd", "usd_lcu"]:
            raise ValueError("Direction must be 'lcu_usd' or 'usd_lcu'")

        # load the data
        self.load_data(direction=direction)

        # return the data
        return self._data
