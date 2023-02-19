import pandas as pd
import pytest

from pydeflate.tools import exchange


@pytest.fixture
def valid_source() -> str:
    """Return a valid source for testing."""
    return "imf"


@pytest.fixture
def valid_columns() -> list:
    """Return a valid list of columns for testing."""
    return ["iso_code", "value", "date"]


@pytest.fixture
def valid_value_column() -> str:
    """Return a valid value column for testing."""
    return "value"


@pytest.fixture
def valid_date_column() -> str:
    """Return a valid date column for testing."""
    return "date"


@pytest.fixture
def test_df() -> pd.DataFrame:
    """Return a test dataframe"""
    return pd.DataFrame(
        {
            "iso_code": ["USA", "FRA", "GTM"],
            "value": [100, 100, 100],
            "date": ["2020-01-01", "2020-01-01", "2020-01-01"],
        }
    ).astype({"date": "datetime64[ns]"})


def test_check_key_errors_invalid_source(
    valid_columns, valid_date_column, valid_value_column
) -> None:
    with pytest.raises(KeyError):
        exchange._check_key_errors(
            rates_source="xxx",
            columns=valid_columns,
            value_column=valid_value_column,
            date_column=valid_date_column,
        )


def test_check_key_errors_invalid_value_column(
    valid_columns, valid_source, valid_date_column
) -> None:

    with pytest.raises(KeyError):
        exchange._check_key_errors(
            rates_source=valid_source,
            columns=valid_columns,
            value_column="xxx",
            date_column=valid_date_column,
        )


def test_check_key_errors_invalid_date_column(
    valid_columns, valid_source, valid_value_column
) -> None:

    with pytest.raises(KeyError):
        exchange._check_key_errors(
            rates_source=valid_source,
            columns=valid_columns,
            value_column=valid_value_column,
            date_column="xxx",
        )


def test__check_key_errors_all_valid(
    valid_source, valid_columns, valid_date_column, valid_value_column
) -> None:

    # test all valid
    exchange._check_key_errors(
        rates_source=valid_source,
        columns=valid_columns,
        value_column=valid_value_column,
        date_column=valid_date_column,
    )


def test_exchange_source_target_equal(test_df) -> None:
    """Test that when the source and target currencies are equal, the
    original dataframe is returned"""

    # test source and target equal
    result = exchange.exchange(
        df=test_df,
        source_currency="USA",
        target_currency="USA",
        rates_source="imf",
        value_column="value",
        date_column="date",
    )

    pd.testing.assert_frame_equal(result, test_df)


def test_exchange_source_target_equal_cols_differ(test_df) -> None:
    """Test that when the source and target currencies are equal, the
    original dataframe is returned"""

    # test source and target equal
    result = exchange.exchange(
        df=test_df,
        source_currency="USA",
        target_currency="USA",
        rates_source="imf",
        value_column="value",
        target_column="value2",
        date_column="date",
    )

    assert "value2" in result.columns


def test_exchange_cols_order_preserved(test_df) -> None:
    """Test that the order of columns is preserved"""

    # test source and target equal
    result = exchange.exchange(
        df=test_df,
        source_currency="USA",
        target_currency="FRA",
        rates_source="imf",
        value_column="value",
        target_column="value2",
        date_column="date",
    )

    assert result.columns[0] == "iso_code"
    assert result.columns[1] == "value"
    assert result.columns[2] == "date"
    assert result.columns[3] == "value2"


def test_exchange_date_integer(test_df) -> None:

    df_ = test_df.assign(date=test_df.date.dt.year)

    # test source and target equal
    result_date = exchange.exchange(
        df=test_df,
        source_currency="USA",
        target_currency="FRA",
        rates_source="imf",
        value_column="value",
        target_column="value2",
        date_column="date",
    )

    result_int = exchange.exchange(
        df=df_,
        source_currency="USA",
        target_currency="FRA",
        rates_source="imf",
        value_column="value",
        target_column="value2",
        date_column="date",
    )

    # test that the results are the same
    pd.testing.assert_series_equal(result_date.value2, result_int.value2)

    # test types are preserved
    assert result_date.date.dtype == "datetime64[ns]"
    assert result_int.date.dtype == "int64"


def test_exchange_target_lcu(test_df) -> None:
    """Test that the target currency can be set to LCU"""

    result = exchange.exchange(
        df=test_df,
        source_currency="USA",
        target_currency="LCU",
        rates_source="imf",
        value_column="value",
        date_column="date",
    )

    assert result.query("iso_code == 'USA'").value.sum() == pytest.approx(100)
    assert result.query("iso_code == 'FRA'").value.sum() == pytest.approx(87.62, 1e-2)
    assert result.query("iso_code == 'GTM'").value.sum() == pytest.approx(772, 1e-2)


def test_exchange_dac_ids(test_df) -> None:
    df_ = test_df.assign(dac_id=[302, 4, 347])

    result = exchange.exchange(
        df=df_,
        source_currency="USA",
        target_currency="LCU",
        rates_source="oecd_dac",
        id_column="dac_id",
        id_type="DAC",
        value_column="value",
        date_column="date",
    )

    assert result.query("iso_code == 'USA'").value.sum() == pytest.approx(100)
    assert result.query("iso_code == 'FRA'").value.sum() == pytest.approx(87.62, 1e-2)
    assert result.query("iso_code == 'GTM'").value.sum() == pytest.approx(100)