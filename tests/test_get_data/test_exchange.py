from unittest.mock import patch

import pandas as pd
import pytest

from pydeflate.get_data.exchange_data import (
    ExchangeIMF,
    ExchangeOECD,
    ExchangeWorldBank,
)


def mock_load_data(self, value_name: str = "value"):
    self._data = pd.DataFrame(
        {
            "year": [
                pd.Timestamp("2020-01-01"),
                pd.Timestamp("2020-01-01"),
                pd.Timestamp("2021-01-01"),
                pd.Timestamp("2021-01-01"),
            ],
            "iso_code": ["USA", "EMU", "USA", "EMU"],
            value_name: [100, 110, 105, 115],
        }
    )
    return self


def mock_load_data_func(self, value_name: str = "value"):
    def load_data(*args, **kwargs):
        self._data = pd.DataFrame(
            {
                "year": [
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2021-01-01"),
                    pd.Timestamp("2021-01-01"),
                ],
                "iso_code": ["USA", "EMU", "USA", "EMU"],
                value_name: [100, 110, 105, 115],
            }
        )

    return load_data


def mock_implied_exchange():
    def load(*args, **kwargs) -> pd.DataFrame:
        data = pd.DataFrame(
            {
                "year": [
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2021-01-01"),
                    pd.Timestamp("2021-01-01"),
                ],
                "iso_code": ["USA", "EMU", "USA", "EMU"],
                "value": [100, 110, 105, 115],
            }
        )
        if kwargs["direction"] == "lcu_usd":
            return data

        data.value = 1 / data.value
        return data

    return load


# ------------------------- UPDATE -------------------------


@patch("pydeflate.get_data.oecd_data.update_dac1")
def test_exchange_oecd_update(mock_update_dac1):
    ExchangeOECD().update()
    mock_update_dac1.assert_called_once()


@patch("pydeflate.get_data.exchange_data.update_world_bank_data")
def test_exchange_world_bank_update(mock_update_world_bank):
    ExchangeWorldBank().update()
    mock_update_world_bank.assert_called_once()


@patch("pydeflate.get_data.exchange_data.IMF.update")
def test_exchange_imf_update(mock_update_imf):
    ExchangeIMF().update()
    mock_update_imf.assert_called_once()


# ------------------------- LOAD DATA, Found -------------------------


def test_oecd_load_data_file_found():
    self = ExchangeOECD()

    # arrange
    exchange_rates = pd.DataFrame({"USD": [1.0, 1.1, 1.2], "EUR": [0.9, 0.8, 0.7]})
    read_feather_mock = patch("pandas.read_feather", return_value=exchange_rates)

    # act
    with read_feather_mock as rf_mock:
        self.load_data()

    # assert
    rf_mock.assert_called_once()
    assert self._data.equals(exchange_rates)


def test_wb_load_data_file_found():
    self = ExchangeWorldBank()

    # arrange
    exchange_rates = pd.DataFrame({"USD": [1.0, 1.1, 1.2], "EUR": [0.9, 0.8, 0.7]})
    read_feather_mock = patch("pandas.read_csv", return_value=exchange_rates)

    # act
    with read_feather_mock as rf_mock:
        self.load_data()

    # assert
    rf_mock.assert_called_once()
    assert self._data.equals(exchange_rates)


def test_imf_load_data_file_found():
    self = ExchangeIMF()

    # arrange
    exchange_rates = pd.DataFrame({"USD": [1.0, 1.1, 1.2], "EUR": [0.9, 0.8, 0.7]})
    read_feather_mock = patch("pydeflate.get_data.exchange_data.IMF.implied_exchange")

    # act
    with read_feather_mock as rf_mock:
        self.load_data()

    # assert
    rf_mock.assert_called_once()
    assert self._data.equals(exchange_rates)


# ------------------------- LOAD DATA, Not Found -------------------------


@patch("pydeflate.get_data.oecd_data.update_dac1")
@patch("pandas.read_feather", side_effect=FileNotFoundError)
def test_oecd_load_data_file_not_found(path, dac_update):
    self = ExchangeOECD()

    with pytest.raises(FileNotFoundError):
        self.load_data()

    # assert
    dac_update.assert_called_once()


@patch("pydeflate.get_data.exchange_data.update_world_bank_data")
@patch("pandas.read_csv", side_effect=FileNotFoundError)
def test_wb_load_data_file_not_found(path, wb_update):
    self = ExchangeWorldBank()

    with pytest.raises(FileNotFoundError):
        self.load_data()

    # assert
    wb_update.assert_called_once()


@patch(
    "pydeflate.get_data.exchange_data.IMF.implied_exchange",
    side_effect=FileNotFoundError,
)
@patch("pandas.read_feather", side_effect=FileNotFoundError)
def test_imf_load_data_file_not_found(path, wb_update):
    self = ExchangeIMF()

    with pytest.raises(FileNotFoundError):
        self.load_data()

    # assert
    wb_update.assert_called_once()


# ------------------------- GET USD EXCHANGE -------------------------


# ------------------------- GET USD EXCHANGE, not loaded -------------------------


def test_oecd_get_usd_exchange_data_not_loaded():
    # arrange
    self = ExchangeOECD()

    # Check that data is not loaded
    assert self._data is None

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeOECD.load_data",
        new_callable=mock_load_data,
        self=self,
        value_name="exchange",
    )

    # act
    with new_load:
        self.usd_exchange_rate()

    # assert
    assert self._data is not None


def test_world_bank_wrong_method():

    # arrange
    with pytest.raises(ValueError):
        ExchangeWorldBank(method="xxx")


def test_world_bank_get_usd_exchange_data_not_loaded():

    # arrange
    self = ExchangeWorldBank()
    self_test = ExchangeWorldBank()

    # Check that data is not loaded
    assert self._data is None

    # act
    with patch(
        "pydeflate.get_data.exchange_data.ExchangeWorldBank.load_data",
        new_callable=mock_load_data_func,
        self=self,
    ):
        self.usd_exchange_rate()

    # assert
    assert self._data is not None


# ----------------------- GET USD EXCHANGE, invalid direction ------------------------


def test_oecd_get_usd_exchange_invalid_direction():
    self = ExchangeOECD()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeOECD.load_data",
        new_callable=mock_load_data,
        self=self,
        value_name="exchange",
    )
    with pytest.raises(ValueError), new_load:
        self.usd_exchange_rate(direction="invalid")


def test_world_bank_get_usd_exchange_invalid_direction():
    self = ExchangeWorldBank()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeWorldBank.load_data",
        new_callable=mock_load_data,
        self=self,
    )
    with pytest.raises(ValueError), new_load:
        self.usd_exchange_rate(direction="invalid")


def test_imf_get_usd_exchange_invalid_direction():
    self = ExchangeIMF()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeIMF.load_data",
        new_callable=mock_load_data,
        self=self,
    )
    with pytest.raises(ValueError), new_load:
        self.usd_exchange_rate(direction="invalid")


# ------------------------- GET USD EXCHANGE, lcu_usd -------------------------


def test_oecd_get_usd_exchange_lcu_usd():

    # arrange
    self = ExchangeOECD()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeOECD.load_data",
        new_callable=mock_load_data,
        self=self,
        value_name="exchange",
    )
    # act
    with new_load:
        result = self.usd_exchange_rate(direction="lcu_usd")

    # assert that original data is not modified
    assert result.query("iso_code == 'USA' and year.dt.year ==2021").value.item() == 105


def test_world_bank_get_usd_exchange_lcu_usd():

    # arrange
    self = ExchangeWorldBank()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeWorldBank.load_data",
        new_callable=mock_load_data,
        self=self,
    )
    # act
    with new_load:
        result = self.usd_exchange_rate(direction="lcu_usd")

    # assert that original data is not modified
    assert result.query("iso_code == 'USA' and year.dt.year ==2021").value.item() == 105


def test_imf_get_usd_exchange_lcu_usd():

    # arrange
    self = ExchangeIMF()

    new_load = patch(
        "pydeflate.get_data.exchange_data.IMF.implied_exchange",
        new_callable=mock_implied_exchange,
    )
    # act
    with new_load:
        result = self.usd_exchange_rate(direction="lcu_usd")

    # assert that original data is not modified
    assert result.query("iso_code == 'USA' and year.dt.year ==2021").value.item() == 105


# ------------------------- GET USD EXCHANGE, usd_lcu -------------------------


def test_oecd_get_usd_exchange_usd_lcu():
    # arrange
    self = ExchangeOECD()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeOECD.load_data",
        new_callable=mock_load_data,
        self=self,
        value_name="exchange",
    )
    # act
    with new_load:
        result = self.usd_exchange_rate(direction="usd_lcu")

    # assert that original data is not modified
    assert result.query(
        "iso_code == 'USA' and year.dt.year ==2021"
    ).value.item() == pytest.approx(0.009524, 1e-3)


def test_world_bank_get_usd_exchange_usd_lcu():
    # arrange
    self = ExchangeWorldBank()

    new_load = patch(
        "pydeflate.get_data.exchange_data.ExchangeWorldBank.load_data",
        new_callable=mock_load_data,
        self=self,
    )
    # act
    with new_load:
        result = self.usd_exchange_rate(direction="usd_lcu")

    # assert that original data is not modified
    assert result.query(
        "iso_code == 'USA' and year.dt.year ==2021"
    ).value.item() == pytest.approx(0.009524, 1e-3)


def test_imf_get_usd_exchange_usd_lcu():

    # arrange
    self = ExchangeIMF()

    new_load = patch(
        "pydeflate.get_data.exchange_data.IMF.implied_exchange",
        new_callable=mock_implied_exchange,
    )
    # act
    with new_load:
        result = self.usd_exchange_rate(direction="usd_lcu")

    # assert that original data is not modified
    assert result.query(
        "iso_code == 'USA' and year.dt.year ==2021"
    ).value.item() == pytest.approx(0.009524, 1e-3)
