import warnings
from dataclasses import dataclass

import pandas as pd
from oda_reader import download_dac1

from pydeflate.get_data.deflate_data import Data
from pydeflate.get_data.exchange_data import ExchangeOECD
from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger
from pydeflate.tools.update_data import update_update_date
from pydeflate.utils import oecd_codes

warnings.simplefilter("ignore", Warning, lineno=1013)


def _compute_deflators_and_exchange(data: pd.DataFrame) -> pd.DataFrame:
    return data.assign(
        exchange=lambda d: round(d.N / d.A, 5),
        deflator=lambda d: round(100 * d.A / d.D, 6),  # implied deflator
        iso_code=lambda d: d.donor_code.map(oecd_codes()),
        year=lambda d: pd.to_datetime(d.year, format="%Y"),
    ).assign(exchange=lambda d: d.exchange.fillna(1))


def _clean_dac1(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DAC1 to keep only relevant information for deflators and exchange.

    Args:
        df: the dataframe to clean

    Returns:
        A cleaned dataframe
    """

    # Columns to keep and rename
    cols = {"amounttype_code": "type", "aidtype_code": "aid", "flows_code": "flow"}

    # Get only the official definition of the data
    query = (
        "(aid == 1010 & flow == 1140 & year <2018 ) | "
        "(aid == 11010 & flow == 1160 & year >=2018)"
    )

    # Clean the data
    data = (
        df.rename(columns=cols)
        .query(query)
        .filter(["donor_code", "type", "year", "value"], axis=1)
        .pivot(index=["donor_code", "year"], columns=["type"], values="value")
        .reset_index()
    )

    data = (
        data.pipe(_compute_deflators_and_exchange)
        .dropna(subset=["iso_code"])
        .filter(["iso_code", "year", "exchange", "deflator"], axis=1)
        .reset_index(drop=True)
    )

    return data


def update_dac1() -> None:
    """Update dac1 data from OECD site and save as feather"""

    # Use oda_reader to get the data
    df = download_dac1(
        filters={"measure": ["1010", "11010"], "flow_type": ["1140", "1160"]}
    )

    # Clean the data
    df = df.pipe(_clean_dac1)

    # Save the data
    df.to_feather(PYDEFLATE_PATHS.data / "pydeflate_dac1.feather")

    # Update the update date
    update_update_date("OECD DAC")


def _identify_base_year(df: pd.DataFrame) -> int:
    return (
        df.query("iso_code in ['FRA','GBR','USA','CAN','DEU','EUI']")
        .groupby(["year"], as_index=False)
        .value.mean(numeric_only=True)
        .round(2)
        .loc[lambda d: d.value == 100.00]
        .year.dt.year.item()
    )


def _calculate_price_deflator(deflators_df: pd.DataFrame) -> pd.DataFrame:
    return deflators_df.assign(
        value=lambda d: round(d.value_dac * d.value_exchange / 100, 6)
    ).filter(["iso_code", "year", "indicator", "value"], axis=1)


@dataclass
class OECD(Data):
    """An object to download and return the latest OECD DAC deflators data."""

    def __post_init__(self):
        self._available_methods = {"dac_deflator": "oecd_dac"}

    def update(self, **kwargs) -> None:
        update_dac1()

    def load_data(self, **kwargs) -> None:
        """Load the OECD DAC price deflators data.

        If the data is not found, it will be downloaded.
        DAC deflators are transformed into price deflators by using the
        implied exchange rate information from the OECD DAC data.

        The deflators that are loaded is therefore *not* the DAC deflator,
        but the price deflator used to produce the DAC deflators.

        """
        try:
            d_ = pd.read_feather(PYDEFLATE_PATHS.data / "pydeflate_dac1.feather")
        except FileNotFoundError:
            logger.info("Data not found, downloading...")
            self.update()
            self.load_data()
            return

        d_ = d_.assign(indicator="oecd_dac").rename(columns={"deflator": "value"})

        # Identify base year
        base_year = _identify_base_year(d_)

        # Load exchange deflators
        exchange_deflator = ExchangeOECD().exchange_deflator(
            source_iso="USA", target_iso="USA", base_year=base_year
        )

        # Merge deflators and exchange deflators
        deflators_df = d_.merge(
            exchange_deflator,
            on=["iso_code", "year"],
            how="left",
            suffixes=("_dac", "_exchange"),
        )

        # Calculate the price deflator
        self._data = _calculate_price_deflator(deflators_df=deflators_df)
