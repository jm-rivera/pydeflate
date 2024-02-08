import pandas as pd
import pytest

from pydeflate.deflate.deflator import Deflator
from pydeflate.get_data.deflators.deflate_data import Data
from pydeflate.get_data.exchange.exchange_data import Exchange


@pytest.fixture
def exchange_obj():
    class MyExchange(Exchange):
        def usd_exchange_rate(self, direction: str = "lcu_to_uds") -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "iso_code": ["USA", "FRA", "GTM"],
                    "value": [1, 0.9, 7.8],
                    "year": ["2020-01-01", "2020-01-01", "2020-01-01"],
                }
            ).astype({"year": "datetime64[ns]"})

        def load_data(self, **kwargs) -> None:
            pass

        def update(self):
            pass

    return MyExchange(method=None)


@pytest.fixture
def deflator_obj():
    class MyData(Data):
        def available_methods(self) -> dict:
            self._available_methods = {"GDP": "GDP"}
            return self._available_methods

        def update(self, **kwargs) -> None:
            pass

        def load_data(self, **kwargs) -> None:
            self._data = pd.DataFrame(
                {
                    "iso_code": ["USA", "FRA", "GTM"],
                    "value": [100, 100, 100],
                    "year": ["2020-01-01", "2020-01-01", "2020-01-01"],
                    "indicator": ["GDP", "GDP", "GDP"],
                }
            ).astype({"year": "datetime64[ns]"})

    return MyData()


@pytest.fixture
def deflator_obj_single():
    class MyData(Data):
        def available_methods(self) -> dict:
            self._available_methods = {"GDP": "GDP"}
            return self._available_methods

        def update(self, **kwargs) -> None:
            pass

        def load_data(self, **kwargs) -> None:
            self._data = pd.DataFrame(
                {
                    "iso_code": ["USA", "USA", "USA"],
                    "value": [100, 105, 110],
                    "year": ["2020-01-01", "2021-01-01", "2022-01-01"],
                    "indicator": ["GDP", "GDP", "GDP"],
                }
            ).astype({"year": "datetime64[ns]"})

    return MyData()


@pytest.fixture
def exchange_obj_single():
    class MyExchange(Exchange):
        def usd_exchange_rate(self, direction: str = "lcu_to_uds") -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "iso_code": ["USA", "USA", "USA"],
                    "value": [1, 1, 1],
                    "year": ["2020-01-01", "2021-01-01", "2022-01-01"],
                }
            ).astype({"year": "datetime64[ns]"})

        def load_data(self, **kwargs) -> None:
            pass

        def update(self):
            pass

    return MyExchange(method=None)


def test_deflator_class_100(exchange_obj, deflator_obj):
    base_year = 2020
    source_currency = "USA"
    target_currency = "USA"
    deflator_method = "GDP"

    deflator = Deflator(
        base_year=base_year,
        exchange_obj=exchange_obj,
        deflator_obj=deflator_obj,
        deflator_method=deflator_method,
        source_currency=source_currency,
        target_currency=target_currency,
    )

    # Test result is 100
    result = deflator.get_deflator()
    assert result.query("iso_code == 'USA'").deflator.sum() == pytest.approx(100)
    assert result.query("iso_code == 'FRA'").deflator.sum() == pytest.approx(100)
    assert result.query("iso_code == 'GTM'").deflator.sum() == pytest.approx(100)


def test_deflator_class_exchange(exchange_obj, deflator_obj):
    base_year = 2020
    source_currency = "GTM"
    target_currency = "USA"
    deflator_method = "GDP"

    deflator = Deflator(
        base_year=base_year,
        exchange_obj=exchange_obj,
        deflator_obj=deflator_obj,
        deflator_method=deflator_method,
        source_currency=source_currency,
        target_currency=target_currency,
    )

    # Test result is 100
    result = deflator.get_deflator()
    assert result.query("iso_code == 'USA'").deflator.sum() == pytest.approx(780)
    assert result.query("iso_code == 'FRA'").deflator.sum() == pytest.approx(780)
    assert result.query("iso_code == 'GTM'").deflator.sum() == pytest.approx(780)


def test_deflator_class_current(exchange_obj_single, deflator_obj_single):
    base_year = 2021
    source_currency = "USA"
    target_currency = "USA"
    deflator_method = "GDP"

    deflator_const = Deflator(
        base_year=base_year,
        exchange_obj=exchange_obj_single,
        deflator_obj=deflator_obj_single,
        deflator_method=deflator_method,
        source_currency=source_currency,
        target_currency=target_currency,
        to_current=False,
    )

    deflator_current = Deflator(
        base_year=base_year,
        exchange_obj=exchange_obj_single,
        deflator_obj=deflator_obj_single,
        deflator_method=deflator_method,
        source_currency=source_currency,
        target_currency=target_currency,
        to_current=True,
    )

    # Test result is 100
    result_const = deflator_const.get_deflator()
    result_current = deflator_current.get_deflator()

    assert result_const.query("year.dt.year == 2020").deflator.sum() == pytest.approx(
        100 / (result_current.query("year.dt.year == 2020").deflator.sum() / 100)
    )

    assert result_const.query("year.dt.year == 2021").deflator.sum() == pytest.approx(
        100 / (result_current.query("year.dt.year == 2021").deflator.sum() / 100)
    )

    assert result_const.query("year.dt.year == 2022").deflator.sum() == pytest.approx(
        100 / (result_current.query("year.dt.year == 2022").deflator.sum() / 100)
    )
