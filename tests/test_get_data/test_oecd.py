import io

import pandas as pd
import requests

from pydeflate.get_data.oecd_data import (
    _clean_dac1,
    _download_bulk_file,
    _read_zip_content,
)


def mock_zip_file(sep: str = ",", file_name: str = "test.csv") -> bytes:
    import zipfile as zf

    # Create a mock CSV file with test data
    file = io.StringIO()
    file.write(f"column1{sep}column2{sep}column3\n")
    file.write(f"value1{sep}1.23{sep}1.4\n")
    file.write(f"value2{sep}2.34{sep}5.6\n")
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
    assert "column1" in df.columns
    assert "column2" in df.columns


def test__download_bulk_file(monkeypatch):
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

    monkeypatch.setattr(requests, "get", mock_requests_get)

    result = _download_bulk_file("https://stats.oecd.org/")

    assert result == b"test content"


def test_clean_dac1():
    # Create a sample dataframe
    df = pd.DataFrame(
        {
            "DONOR": [4, 4, 4, 12, 12, 12],
            "AMOUNTTYPE": ["A", "D", "N", "A", "D", "N"],
            "AIDTYPE": [1010, 1010, 1010, 11010, 11010, 11010],
            "Year": [2017, 2017, 2017, 2019, 2019, 2019],
            "FLOWS": [1140, 1140, 1140, 1160, 1160, 1160],
            "Value": [10, 10, 30, 20, 22, 40],
        }
    )

    # Expected output
    expected = pd.DataFrame(
        {
            "iso_code": ["FRA", "GBR"],
            "year": [pd.Timestamp("2017-01-01"), pd.Timestamp("2019-01-01")],
            "exchange": [3.0, 2.0],
            "deflator": [100.000000, 90.909091],
        }
    )

    # Test the function
    result = _clean_dac1(df)

    # Assert that the result is as expected
    pd.testing.assert_frame_equal(
        result, expected, check_index_type=False, check_names=False
    )
