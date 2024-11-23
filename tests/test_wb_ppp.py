import pandas as pd

from pydeflate import wb_exchange_ppp
from pydeflate.deflate.deflators import wb_ppp_deflate

data_usd = {
    "year": [2020, 2021, 2022, 2023],
    "iso_code": ["GTM"] * 4,
    "currency": ["USD"] * 4,
    "value": [77715183063, 86053083476, 95003330316, 102050473864],
    "expected_value": [190006601695, 207137814681, 230852981355, 247604803199],
}

df_usd = pd.DataFrame(data_usd)

data_lcu = {
    "year": [2020, 2021, 2022, 2023],
    "iso_code": ["GTM"] * 4,
    "currency": ["GTM"] * 4,
    "value": [600089443300, 665567936200, 736108984100, 799259311300],
    "expected_value": [190006601695, 207137814681, 230852981355, 247604803199],
}

df_lcu = pd.DataFrame(data_lcu)


data_lcu_rev = {
    "year": [2020, 2021, 2022, 2023],
    "iso_code": ["GTM"] * 4,
    "currency": ["PPP"] * 4,
    "expected_value": [600089443300, 665567936200, 736108984100, 799259311300],
    "value": [190006601695, 207137814681, 230852981355, 247604803199],
}

df_lcu_rev = pd.DataFrame(data_lcu_rev)

data_ppp = {
    "year": [2020, 2021, 2022, 2023],
    "iso_code": ["GTM"] * 4,
    "currency": ["PPP"] * 4,
    "value": [190006601695, 207137814681, 230852981355, 247604803199],
    "expected_value": [191789996581, 207137814681, 215667758525, 223182668633],
}

df_ppp = pd.DataFrame(data_ppp)


data_lcu_to_constant = {
    "year": [2020, 2021, 2022, 2023],
    "iso_code": ["GTM"] * 4,
    "currency": ["GTM"] * 4,
    "value": [600089443300, 665567936200, 736108984100, 799259311300],
    "expected_value": [191789996581, 207137814681, 215667758525, 223182668633],
}

df_lcu_to_constant = pd.DataFrame(data_lcu_to_constant)


data_usd_to_constant = {
    "year": [2020, 2021, 2022, 2023],
    "iso_code": ["GTM"] * 4,
    "currency": ["USD"] * 4,
    "value": [77715183063, 86053083476, 95003330316, 102050473864],
    "expected_value": [191789996581, 207137814681, 215667758525, 223182668633],
}

df_usd_to_constant = pd.DataFrame(data_usd_to_constant)


def run_test_to_ppp(
    data,
    source_currency,
    tolerance=0.01,
    target_value_column="valueppp",
    reversed_=False,
):

    test_df = wb_exchange_ppp(
        data=data,
        source_currency=source_currency,
        id_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column=target_value_column,
        reversed_=reversed_,
    )

    # Calculate the percentage deviation
    deviations = abs(
        (test_df[target_value_column] - test_df["expected_value"])
        / test_df["expected_value"]
    )

    # Filter out rows where value is NaN and deviations exceed tolerance
    mask = test_df[target_value_column].notna() & (deviations >= tolerance)
    failing_rows = test_df[mask]

    # Assert that no rows exceed the tolerance
    assert failing_rows.empty, (
        f"Deviation exceeded {tolerance*100:.2f}% in the following "
        f"donors:\n{failing_rows['iso_code'].unique()}"
    )


def run_test_to_constant_ppp(
    data,
    source_currency,
    base_year=2021,
    tolerance=0.01,
    target_value_column="valueppp",
    reversed_=False,
):

    test_df = wb_ppp_deflate(
        data=data,
        base_year=base_year,
        source_currency=source_currency,
        id_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column=target_value_column,
        reversed_=reversed_,
    )

    # Calculate the percentage deviation
    deviations = abs(
        (test_df[target_value_column] - test_df["expected_value"])
        / test_df["expected_value"]
    )

    # Filter out rows where value is NaN and deviations exceed tolerance
    mask = test_df[target_value_column].notna() & (deviations >= tolerance)
    failing_rows = test_df[mask]

    # Assert that no rows exceed the tolerance
    assert failing_rows.empty, (
        f"Deviation exceeded {tolerance*100:.2f}% in the following "
        f"donors:\n{failing_rows['iso_code'].unique()}"
    )


def test_usd_to_ppp():
    run_test_to_ppp(data=df_usd, source_currency="USA", tolerance=0.01)


def test_lcu_to_ppp():
    run_test_to_ppp(data=df_lcu, source_currency="LCU", tolerance=0.01)


def test_lcu_to_ppp_reversed():
    run_test_to_ppp(
        data=df_lcu_rev, source_currency="LCU", tolerance=0.01, reversed_=True
    )


def test_ppp_to_constant_ppp():
    run_test_to_constant_ppp(data=df_ppp, source_currency="PPP", tolerance=0.01)


def test_lcu_to_constant_ppp():
    run_test_to_constant_ppp(
        data=df_lcu_to_constant, source_currency="LCU", tolerance=0.01
    )


def test_usd_to_constant_ppp():
    run_test_to_constant_ppp(
        data=df_usd_to_constant, source_currency="USD", tolerance=0.01
    )
