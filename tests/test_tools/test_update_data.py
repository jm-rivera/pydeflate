from unittest.mock import MagicMock, patch

import pytest
from pydeflate.tools import update_data
from pydeflate import pydeflate_config, set_pydeflate_path


set_pydeflate_path(pydeflate_config.PYDEFLATE_PATHS.test_data)


def test_diff_from_today() -> None:
    from datetime import datetime, timedelta

    today = datetime.today()
    yesterday = today - timedelta(days=1)

    assert update_data._diff_from_today(yesterday) == 1


def test_warn_updates(caplog) -> None:
    with patch("json.load", return_value={"IMF": "2021-02-14"}):
        update_data.warn_updates()

    assert "IMF" in caplog.text


def test_update_date_no_file(mocker):
    outfile_mock = MagicMock()
    mocker.patch("builtins.open", return_value=outfile_mock)

    with patch("pathlib.Path.exists", return_value=False), pytest.raises(TypeError):
        update_data.update_update_date("IMF")


def test_update_date_file_exists(mocker):
    outfile_mock = MagicMock()
    mocker.patch("builtins.open", return_value=outfile_mock)

    with patch("json.load", return_value={"IMF": "2027-02-14"}) as jload:
        update_data.update_update_date("IMF")

    assert jload.called


class MockUpdate:
    pass


@patch("pydeflate.get_data.imf_data.IMF")
@patch("pydeflate.get_data.oecd_data.OECD")
@patch("pydeflate.get_data.wb_data.WorldBank")
def test_update_all_data(mock_imf, mock_oecd, mock_wb):
    update_data.update_all_data()
