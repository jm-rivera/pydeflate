import pandas as pd

from pydeflate import oecd_dac_deflate

data = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [12] * 4,
    "currency": ["USD"] * 4,
    "prices": ["current"] * 4,
    "value": [18568.19, 15712.01, 15761.81, 19110.59],
    "expected_value": [16312, 12885, 13717, 15374],
}

df = pd.DataFrame(data)

data_usd = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [302] * 4,
    "currency": ["USD"] * 4,
    "prices": ["current"] * 4,
    "value": [35576.31, 47804.8, 60522.41, 66040.03],
    "expected_value": [41326, 53097, 62800, 66040],
}


df_usd = pd.DataFrame(data_usd)

data_eur = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [742] * 4,
    "currency": ["EUR"] * 4,
    "prices": ["current"] * 4,
    "value": [1974, 2429, 2672, 2896],
    "expected_value": [1995, 2403, 2619, 2896],
}
df_eur = pd.DataFrame(data_eur)


data_can = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [5] * 4,
    "currency": ["CAD"] * 4,
    "prices": ["current"] * 4,
    "value": [38503, 41707, 46393, 49495],
    "expected_value": [31404, 34049, 38957, 36682],
}
df_can = pd.DataFrame(data_can)


data_lcu = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [4] * 4,
    "currency": ["EUR"] * 4,
    "prices": ["current"] * 4,
    "value": [12394, 13112, 15228, 14266],
    "expected_value": [13625, 14210, 16031, 14266],
}
df_lcu = pd.DataFrame(data_lcu)

data_eui_gbp = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [918] * 4,
    "currency": ["USD"] * 4,
    "prices": ["current"] * 4,
    "value": [19568, 19054, 22534, 26926],
    "expected_value": [16882, 15490, 19693, 21662],
}

df_eui_gbp = pd.DataFrame(data_eui_gbp)

data_aus_gbp = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [801] * 4,
    "currency": ["USD"] * 4,
    "prices": ["current"] * 4,
    "value": [2869, 3546, 3046, 3253],
    "expected_value": [2629, 2822, 2432, 2617],
}

df_aus_gbp = pd.DataFrame(data_aus_gbp)

usd_to = {
    "year": [2020, 2021, 2022, 2023],
    "indicator": ["total_oda_official_definition"] * 4,
    "donor_code": [5] * 4,
    "currency": ["USD"] * 4,
    "prices": ["current"] * 4,
    "value": [28707.88, 33272.39, 35640.06, 36682.34],
    "expected_value": [25264, 27392, 31341, 29511],
}

df_usd_to_gbp = pd.DataFrame(usd_to)



def run_constant_test(
    data,
    source_currency,
    target_currency,
    tolerance=0.05,
    base_year=2023,
    id_column="donor_code",
    target_value_column="value",
):
    """
    Runs a test for deflation calculation with given parameters and tolerance.

    Args:
        data (pd.DataFrame): The input DataFrame containing the data to deflate.
        source_currency (str): The source currency code.
        target_currency (str): The target currency code.
        tolerance (float, optional): The allowed tolerance for deviation. Defaults to 0.05.
        base_year (int, optional): The base year for deflation. Defaults to 2023.
        id_column (str, optional): Column name for IDs. Defaults to "donor_code".
        target_value_column (str, optional): Column name for the target value. Defaults to "value".

    Raises:
        AssertionError: If any row exceeds the tolerance threshold.
    """
    # Perform the deflation calculation
    test_df = oecd_dac_deflate(
        data=data,
        base_year=base_year,
        source_currency=source_currency,
        target_currency=target_currency,
        id_column=id_column,
        use_source_codes=True,
        target_value_column=target_value_column,
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
        f"donors:\n{failing_rows[id_column].unique()}"
    )


# Define test cases with parameters
def test_to_constant():
    run_constant_test(
        data=df, source_currency="USA", target_currency="GBP", tolerance=0.01
    )


def test_to_constant_usd():
    run_constant_test(
        data=df_usd, source_currency="USA", target_currency="USA", tolerance=0.01
    )


def test_to_constant_eur():
    run_constant_test(
        data=df_eur, source_currency="EUR", target_currency="EUR", tolerance=0.02
    )


def test_to_constant_can():
    run_constant_test(
        data=df_can, source_currency="CAN", target_currency="USA", tolerance=0.02
    )


def test_to_constant_lcu():
    run_constant_test(
        data=df_lcu, source_currency="EUR", target_currency="LCU", tolerance=0.02
    )


def test_eui_gbp_constant():
    run_constant_test(
        data=df_eui_gbp, source_currency="USD", target_currency="GBP", tolerance=0.02
    )


def test_aus_gbp_constant():
    run_constant_test(
        data=df_aus_gbp, source_currency="USD", target_currency="GBP", tolerance=0.02
    )


def test_to_constant_gbp():
    run_constant_test(
        data=df_usd_to_gbp, source_currency="USD", target_currency="GBP", tolerance=0.05
    )
