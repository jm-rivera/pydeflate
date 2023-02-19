import io
from unittest.mock import patch

import pandas as pd
import pytest
import requests

from pydeflate.get_data.oecd_data import (
    OECD,
    _calculate_price_deflator,
    _clean_dac1,
    _download_bulk_file,
    _identify_base_year,
    _read_zip_content,
    update_dac1,
)

from pydeflate import pydeflate_config, set_pydeflate_path

set_pydeflate_path(pydeflate_config.PYDEFLATE_PATHS.test_data)


def mock_requests_get(url):
    if "FileView" in url:

        class Response:
            def __init__(self):
                self.status_code = 200

            @property
            def content(self):
                return b"test content"

        return Response()

    class Response:
        def __init__(self):
            self.status_code = 200

        @property
        def text(self):
            return r"<a onclick='location.href='FileView2.aspx?IDFile=123456'></a>"

    return Response()


def mock_zip_file(sep: str = ",", file_name: str = "test.csv") -> bytes:
    import zipfile as zf

    # Create a mock CSV file with test data
    file = io.StringIO()
    file.write(f"DONOR{sep}Year{sep}Value{sep}AIDTYPE{sep}FLOWS{sep}AMOUNTTYPE\n")
    file.write(f"4{sep}2019{sep}1.4{sep}11010{sep}1160{sep}N\n")
    file.write(f"4{sep}2019{sep}1.8{sep}11010{sep}1160{sep}A\n")
    file.write(f"4{sep}2019{sep}1.9{sep}11010{sep}1160{sep}D\n")
    file.write(f"12{sep}2017{sep}2.6{sep}1010{sep}1140{sep}N\n")
    file.write(f"12{sep}2017{sep}1.6{sep}1010{sep}1140{sep}A\n")
    file.write(f"12{sep}2017{sep}5.6{sep}1010{sep}1140{sep}D\n")
    file.seek(0)

    # Create a mock zip file from the mock CSV file
    zip_buffer = io.BytesIO()
    with zf.ZipFile(zip_buffer, "w") as zf:
        zf.writestr(file_name, file.getvalue())

    # Get the binary content of the mock zip file
    request_content = zip_buffer.getvalue()

    return request_content


def test__read_zip_content():
    # Test data: with comma as separator
    request_content = mock_zip_file()  # binary content of the zip file
    file_name = "test.csv"

    # Read the zip file content using the function under test
    df = _read_zip_content(request_content, file_name)

    # Assert that the returned dataframe has the expected columns and data
    assert "Year" in df.columns
    assert "DONOR" in df.columns


def test__read_zip_content_unicode_error():
    # Test data: with comma as separator
    request_content = mock_zip_file()  # binary content of the zip file
    file_name = "test.csv"

    with patch("pandas.read_csv", side_effect=UnicodeDecodeError):
        # Read the zip file content using the function under test
        with pytest.raises((UnicodeDecodeError, TypeError)):
            _read_zip_content(request_content, file_name)


def test__download_bulk_file(monkeypatch):

    monkeypatch.setattr(requests, "get", mock_requests_get)

    result = _download_bulk_file("https://stats.oecd.org/")

    assert result == b"test content"


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "DONOR": [4, 4, 4, 12, 12, 12],
            "AMOUNTTYPE": ["A", "D", "N", "A", "D", "N"],
            "AIDTYPE": [1010, 1010, 1010, 11010, 11010, 11010],
            "Year": [2017, 2017, 2017, 2019, 2019, 2019],
            "FLOWS": [1140, 1140, 1140, 1160, 1160, 1160],
            "Value": [10, 10, 30, 20, 22, 40],
        }
    )


@pytest.fixture
def expected():
    return pd.DataFrame(
        {
            "iso_code": ["FRA", "GBR"],
            "year": [pd.Timestamp("2017-01-01"), pd.Timestamp("2019-01-01")],
            "exchange": [3.0, 2.0],
            "deflator": [100.000000, 90.909091],
        }
    )


def test_clean_dac1(df, expected):

    # Test the function
    result = _clean_dac1(df)

    # Assert that the result is as expected
    pd.testing.assert_frame_equal(
        result, expected, check_index_type=False, check_names=False
    )


def test__update_dac1(monkeypatch):
    def _mock_download_bulk_file():
        def __bulk_file(**kwargs):
            return mock_zip_file(sep=",", file_name="Table1_Data.csv")

        return __bulk_file

    with patch(
        "pydeflate.get_data.oecd_data._download_bulk_file",
        new_callable=_mock_download_bulk_file,
    ), patch("pandas.DataFrame.to_feather", return_value=None) as save, patch(
        "pydeflate.get_data.oecd_data.update_update_date", return_value=None
    ) as date:
        update_dac1()

    assert save.called
    assert date.called


@patch("pydeflate.get_data.oecd_data.update_dac1", return_value=None)
def test_update(mock_update):
    oecd = OECD()
    oecd.update()

    assert mock_update.called


def test_identify_base_year():

    test_df = pd.DataFrame(
        {
            "iso_code": ["FRA", "FRA"],
            "year": [pd.Timestamp("2017-01-01"), pd.Timestamp("2019-01-01")],
            "value": [100, 150],
        }
    )

    result = _identify_base_year(test_df)

    assert result == 2017


def test_calculate_price_def():

    test_df = pd.DataFrame(
        {
            "iso_code": ["FRA", "FRA"],
            "year": [pd.Timestamp("2017-01-01"), pd.Timestamp("2019-01-01")],
            "value_dac": [100, 150],
            "value_exchange": [2, 1],
        }
    )

    result = _calculate_price_deflator(test_df)

    assert result.query("year.dt.year == 2017").value.sum() == pytest.approx(2)
    assert result.query("year.dt.year == 2019").value.sum() == pytest.approx(1.5)


def _mock_read():
    def read_feather(*args, **kwargs):
        global check
        try:
            if check:
                return pd.DataFrame(
                    {
                        "iso_code": ["USA", "USA"],
                        "year": [
                            pd.Timestamp("2017-01-01"),
                            pd.Timestamp("2019-01-01"),
                        ],
                        "exchange": [3.0, 2.0],
                        "deflator": [100.000000, 90.909091],
                    }
                )
        except NameError:
            check = True
            raise FileNotFoundError

    return read_feather


@patch("pandas.read_feather", new_callable=_mock_read)
@patch("pydeflate.get_data.oecd_data.update_dac1", return_value=None)
def test_load_data(update, read):
    oecd = OECD()
    oecd.load_data()

    assert len(oecd._data) > 0
    assert update.called
