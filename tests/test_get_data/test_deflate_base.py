from dataclasses import dataclass

import pandas as pd
import pytest

from pydeflate.get_data.deflators import deflate_data as deflate


@dataclass
class MockData(deflate.Data):
    indicator: str | None = None
    _data: pd.DataFrame = None
    _available_methods: dict | None = None

    def __post_init__(self):
        self._available_methods = {
            "Gross domestic product, deflator": "NGDP_D",
            "gdp_linked": "NY.GDP.DEFL.ZS.AD",
            "oecd_dac": "dac_deflator",
        }

    def update(self, **kwargs) -> None:
        super()

    def load_data(self, **kwargs) -> None:
        d_ = pd.DataFrame(
            {
                "year": [
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2021-01-01"),
                    pd.Timestamp("2021-01-01"),
                ],
                "iso_code": ["USA", "FRA", "USA", "FRA"],
                "value": [100, 110, 105, 115],
            }
        ).assign(indicator=self.indicator)

        self._data = d_


# Shared fixtures
@pytest.fixture
def mock_imf():
    return MockData(indicator="NGDP_D")


@pytest.fixture
def mock_wb():
    return MockData(indicator="NY.GDP.DEFL.ZS.AD")


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


def test_deflate_method_wrong(mock_imf):
    # Test that an error is raised if an incorrect method is passed
    with pytest.raises(ValueError):
        mock_imf.get_method(method="wrong")


def test_deflate_method_columns(mock_imf):
    # Get rates for FRA
    imf = mock_imf.get_method("NGDP_D")

    # Check that only the correct columns are present
    assert set(imf.columns) == {"year", "iso_code", "value"}


def test_deflate_deflator_wrong_method(mock_imf):
    # Test that an error is raised if an incorrect method is passed
    with pytest.raises(ValueError):
        mock_imf.get_deflator(base_year=2020, method="wrong")


def test_deflate_deflator_no_method(mock_imf):
    # Test that an error is raised if no method is passed
    with pytest.raises(ValueError):
        mock_imf.get_deflator(base_year=2020)


def test_deflate_deflator_wrong_base_year(mock_wb):
    # Test that an error is raised if an incorrect base year is passed.
    with pytest.raises(ValueError):
        mock_wb.get_deflator(method="gdp_linked", base_year=2015)


def test_deflate_deflator_columns(mock_wb):
    # Get deflator for FRA
    xd_fr = mock_wb.get_deflator(method="gdp_linked", base_year=2020)

    # Check that only the correct columns are present
    assert set(xd_fr.columns) == {"year", "iso_code", "value"}


def test_deflate_deflator_wb(mock_wb, fr20, fr21, us20, us21):
    # Get rates for FRA
    deflator = mock_wb.get_deflator(method="gdp_linked", base_year=2020)

    assert deflator.query(fr20).value.item() == pytest.approx(100)
    assert deflator.query(fr21).value.item() == pytest.approx(104.54, 1e-3)
    assert deflator.query(us20).value.item() == pytest.approx(100)
    assert deflator.query(us21).value.item() == pytest.approx(105, 1e-3)
