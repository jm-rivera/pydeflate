import pandas as pd
import pytest

from pydeflate.get_data import exchange


class MockExchange(exchange.Exchange):
    def update(self, **kwargs) -> None:
        pass

    def load_data(self, **kwargs) -> None:
        pass

    def usd_exchange_rate(self, direction: str = "lcu_to_usd") -> pd.DataFrame:
        d_ = pd.DataFrame(
            {
                "year": [
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2021-01-01"),
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2021-01-01"),
                ],
                "iso_code": ["USA", "USA", "FRA", "FRA"],
                "value": [1.0, 1.0, 1.15, 1.2],
            }
        )
        if direction == "lcu_to_usd":
            return d_
        else:
            return d_.assign(value=lambda d: 1 / d.value)


# Shared fixtures
@pytest.fixture
def mock_exchange():
    return MockExchange(method="mock")


@pytest.fixture
def fr20():
    return "year.dt.year == 2020 and iso_code == 'FRA'"


@pytest.fixture
def fr21():
    return "year.dt.year == 2021 and iso_code == 'FRA'"


@pytest.fixture
def us20():
    return "year.dt.year == 2020 and iso_code == 'USA'"


@pytest.fixture
def us21():
    return "year.dt.year == 2021 and iso_code == 'USA'"


def test_exchange_rate_wrong_iso(mock_exchange):
    # Test that an error is raised if an incorrect ISO is passed
    with pytest.raises(ValueError):
        mock_exchange.exchange_rate(currency_iso="XXX")


def test_exchange_rate_columns(mock_exchange):
    # Get rates for FRA
    xe_fr = mock_exchange.exchange_rate(currency_iso="FRA")

    # Check that only the correct columns are present
    assert set(xe_fr.columns) == {"year", "iso_code", "value"}


def test_exchange_rate_non_usd(mock_exchange, fr20, fr21, us20, us21):
    # Get rates for FRA
    xe_fr = mock_exchange.exchange_rate(currency_iso="FRA")

    assert xe_fr.query(fr20).value.item() == pytest.approx(1)
    assert xe_fr.query(fr21).value.item() == pytest.approx(1)
    assert xe_fr.query(us20).value.item() == pytest.approx(0.8695, 1e-2)
    assert xe_fr.query(us21).value.item() == pytest.approx(0.8333, 1e-2)


def test_exchange_rate_usd(mock_exchange, fr20, fr21, us20, us21):
    # Get rates for USA
    xe_us = mock_exchange.exchange_rate(currency_iso="USA")

    assert xe_us.query(fr20).value.item() == pytest.approx(1.15)
    assert xe_us.query(fr21).value.item() == pytest.approx(1.20)
    assert xe_us.query(us20).value.item() == pytest.approx(1)
    assert xe_us.query(us21).value.item() == pytest.approx(1)


def test_exchange_deflator_wrong_iso(mock_exchange):
    # Test that an error is raised if an incorrect ISO is passed
    with pytest.raises(ValueError):
        mock_exchange.exchange_deflator(currency_iso="XXX", base_year=2020)


def test_exchange_deflator_wrong_base_year(mock_exchange):
    # Test that an error is raised if an incorrect base year is passed
    with pytest.raises(ValueError):
        mock_exchange.exchange_deflator(currency_iso="USA", base_year=2015)


def test_exchange_delfator_columns(mock_exchange):
    # Get deflator for FRA
    xd_fr = mock_exchange.exchange_deflator(currency_iso="FRA", base_year=2020)

    # Check that only the correct columns are present
    assert set(xd_fr.columns) == {"year", "iso_code", "value"}


def test_exchange_deflator_non_usd(mock_exchange, fr20, fr21, us20, us21):
    # Get rates for FRA
    xe_fr = mock_exchange.exchange_deflator(currency_iso="FRA", base_year=2020)

    assert xe_fr.query(fr20).value.item() == pytest.approx(100)
    assert xe_fr.query(fr21).value.item() == pytest.approx(100)
    assert xe_fr.query(us20).value.item() == pytest.approx(100)
    assert xe_fr.query(us21).value.item() == pytest.approx(95.93, 1e-2)


def test_exchange_deflator_usd(mock_exchange, fr20, fr21, us20, us21):
    # Get rates for USA
    xe_us = mock_exchange.exchange_deflator(currency_iso="USA", base_year=2020)

    assert xe_us.query(fr20).value.item() == pytest.approx(100, 1e-2)
    assert xe_us.query(fr21).value.item() == pytest.approx(104.348, 1e-2)
    assert xe_us.query(us20).value.item() == pytest.approx(100)
    assert xe_us.query(us21).value.item() == pytest.approx(100)
