import pandas as pd
import pytest

from pydeflate import set_pydeflate_path, pydeflate_config
from pydeflate.deflate.deflate import (
    _create_id_col,
    _validate_deflator_method,
    _validate_deflator_source,
    _validate_exchange_method,
    _validate_exchange_source,
    deflate,
)

set_pydeflate_path(pydeflate_config.PYDEFLATE_PATHS.test_data)


def test__validate_deflator_source_bad():
    # bad source
    source = "XXX"
    with pytest.raises(ValueError):
        _validate_deflator_source(source)

    # No source
    with pytest.raises(ValueError):
        _validate_deflator_source(None)


def test__validate_deflator_source_good():
    # good source
    source = "oecd_dac"

    _validate_deflator_source(source)


def test__validate_deflator_method_good():
    deflator_source, deflator_method = "world_bank", "gdp"
    _validate_deflator_method(deflator_source, deflator_method)


def test__validate_deflator_method_default():
    deflator_source, deflator_method = "world_bank", None
    method = _validate_deflator_method(deflator_source, deflator_method)
    assert method == "gdp"


def test__validate_deflator_method_bad():
    deflator_source, deflator_method = "world_bank", "xxx"
    with pytest.raises(ValueError):
        _validate_deflator_method(deflator_source, deflator_method)


def test__validate_exchange_source_good():
    deflator_method, exchange_source = "implicit", "oecd_dac"
    _validate_exchange_source(deflator_method, exchange_source)


def test__validate_exchange_source_pick_default():
    deflator_method, exchange_source = "oecd_dac", None

    method = _validate_exchange_source(deflator_method, exchange_source)

    assert method == "implied"


def test__validate_exchange_source_bad():
    deflator_method, exchange_source = "oecd_dac", "xxx"

    with pytest.raises(ValueError):
        _validate_exchange_source(deflator_method, exchange_source)


def test__validate_exchange_method_good():
    exchange_source, exchange_method = "oecd_dac", "implied"
    result = _validate_exchange_method(exchange_source, exchange_method)

    assert result == "implied"


def test__validate_exchange_method_default():
    exchange_source, exchange_method = "oecd_dac", None
    result = _validate_exchange_method(exchange_source, exchange_method)

    assert result == "implied"


def test__validate_exchange_method_bad():
    exchange_source, exchange_method = "oecd_dac", "xxx"
    with pytest.raises(ValueError):
        _validate_exchange_method(exchange_source, exchange_method)


def test__create_id_col_iso():
    df, id_type, id_column = (
        pd.DataFrame({"iso_code": ["FRA", "GTM", "USA"]}),
        "ISO3",
        "iso_code",
    )
    result = _create_id_col(df, id_type, id_column)

    assert "id_" in result.columns


def test__create_id_col_dac():
    df, id_type, id_column = (
        pd.DataFrame({"code": [4, 12, 500]}),
        "DAC",
        "code",
    )
    result = _create_id_col(df, id_type, id_column)

    assert "id_" in result.columns
    assert len(result.id_.values[0]) == 3


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "iso_code": ["FRA", "FRA", "USA", "USA"],
            "year": [2020, 2021, 2020, 2021],
            "value": [16_013, 16_722, 35_396, 47_528],
        }
    )


@pytest.fixture
def df2current():
    return pd.DataFrame(
        {
            "iso_code": ["FRA", "FRA", "USA", "USA"],
            "year": [2020, 2021, 2020, 2021],
            "value": [16_743, 16_772, 36_809, 47_528],
        }
    )


def test_backward_compatibility(df, caplog):
    deflate(
        df,
        base_year=2020,
        iso_column="iso_code",
        date_column="year",
        source_col="value",
        target_col="value",
        method="gdp",
        source="imf",
        exchange_method="implied",
        exchange_source="oecd_dac",
    )
    assert "iso_column" in caplog.text
    assert "source_col" in caplog.text
    assert "target_col" in caplog.text
    assert "method" in caplog.text
    assert "source" in caplog.text


def test_target_column(df):
    result = deflate(
        df,
        base_year=2020,
        id_column="iso_code",
        date_column="year",
        source_column="value",
        target_column="value_deflate",
        deflator_method="gdp",
        deflator_source="imf",
        exchange_method="implied",
        exchange_source="oecd_dac",
    )
    assert "value_deflate" in result.columns


def test_deflate_results_dac_to_constant(df):
    result = deflate(
        df=df,
        base_year=2021,
        id_column="iso_code",
        date_column="year",
        source_column="value",
        target_column="value_deflate",
        deflator_method="dac_deflator",
        deflator_source="oecd_dac",
        exchange_method="implied",
        exchange_source="oecd_dac",
    )
    assert result.query("iso_code == 'FRA' and year == 2020")[
        "value_deflate"
    ].sum() == pytest.approx(16_743, 1e-4)

    assert result.query("iso_code == 'USA' and year == 2020")[
        "value_deflate"
    ].sum() == pytest.approx(36_809, 1e-4)


def test_deflate_results_dac_to_current(df2current):
    result = deflate(
        df=df2current,
        base_year=2021,
        id_column="iso_code",
        date_column="year",
        source_column="value",
        target_column="value_deflate",
        deflator_method="dac_deflator",
        deflator_source="oecd_dac",
        exchange_method="implied",
        exchange_source="oecd_dac",
        to_current=True,
    )
    assert result.query("iso_code == 'FRA' and year == 2020")[
        "value_deflate"
    ].sum() == pytest.approx(16_013, 1e-4)

    assert result.query("iso_code == 'USA' and year == 2020")[
        "value_deflate"
    ].sum() == pytest.approx(35_396, 1e-4)


def test_deflate_results_imf_to_constant(df):
    result = deflate(
        df=df,
        base_year=2021,
        id_column="iso_code",
        date_column="year",
        source_column="value",
        target_column="value_deflate",
        deflator_method="gdp",
        deflator_source="imf",
        exchange_method="implied",
        exchange_source="imf",
    )
    assert result.query("iso_code == 'FRA' and year == 2020")[
        "value_deflate"
    ].sum() == pytest.approx(16_826, 1e-4)

    assert result.query("iso_code == 'USA' and year == 2020")[
        "value_deflate"
    ].sum() == pytest.approx(36_867, 1e-4)


def test_deflate_results_imf_to_current(df2current):
    result = deflate(
        df=df2current,
        base_year=2021,
        id_column="iso_code",
        date_column="year",
        source_column="value",
        target_column="value_deflate",
        deflator_method="gdp",
        deflator_source="imf",
        exchange_method="implied",
        exchange_source="imf",
        to_current=True,
    )
    assert result.query("iso_code == 'FRA' and year == 2020")[
               "value_deflate"
           ].sum() == pytest.approx(15_933, 1e-4)

    assert result.query("iso_code == 'USA' and year == 2020")[
               "value_deflate"
           ].sum() == pytest.approx(35_340, 1e-4)