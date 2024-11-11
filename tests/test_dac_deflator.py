from pydeflate import oecd_dac_deflate


def get_test_data():
    from oda_reader import download_dac1

    idx = ["year", "donor_code", "donor_name"]

    data = (
        download_dac1(
            start_year=2010, filters={"measure": ["1010"], "flow_type": ["1140"]}
        )
        .filter(idx + ["amounttype_code", "value"])
        .pivot(index=idx, columns="amounttype_code", values="value")
        .reset_index()
        .assign(N=lambda d: d.N.fillna(d.A))
    )

    return data


df = get_test_data()


def test_to_constant(tolerance=0.01):

    # Perform the deflation calculation
    test_df = oecd_dac_deflate(
        data=df,
        base_year=2022,
        source_currency="USA",
        target_currency="USA",
        id_column="donor_code",
        use_source_codes=True,
        value_column="A",
    )

    # Calculate the percentage deviation
    deviations = abs((test_df["value"] - test_df["D"]) / test_df["D"])

    # Filter out rows where D is NaN to avoid unnecessary comparisons
    mask = test_df["D"].notna() & (deviations >= tolerance)
    failing_rows = test_df[mask]

    failing_rows = failing_rows.loc[lambda d: d.donor_code < 20000]

    # Assert that no rows exceed the tolerance
    assert failing_rows.empty, (
        f"Deviation exceeded {tolerance*100:.2f}% in the following"
        f"donors:\n"
        f"{failing_rows.donor_code.unique()}"
    )


def test_to_constant_lcu_USA(tolerance=0.01):

    # Perform the deflation calculation
    test_df = oecd_dac_deflate(
        data=df,
        base_year=2022,
        source_currency="LCU",
        target_currency="USA",
        id_column="donor_code",
        use_source_codes=True,
        value_column="N",
    )

    # Calculate the percentage deviation
    deviations = abs((test_df["value"] - test_df["D"]) / test_df["D"])

    # Filter out rows where D is NaN to avoid unnecessary comparisons
    mask = test_df["D"].notna() & (deviations >= tolerance)
    failing_rows = test_df[mask]

    failing_rows = failing_rows.loc[lambda d: d.donor_code < 20000]

    # Assert that no rows exceed the tolerance
    assert failing_rows.empty, (
        f"Deviation exceeded {tolerance*100:.2f}% in the following"
        f"donors:\n"
        f"{failing_rows.donor_code.unique()}"
    )


def test_to_current(tolerance=0.01):

    # Perform the adjustment to current currency
    test_df = oecd_dac_deflate(
        data=df,
        base_year=2022,
        source_currency="USA",
        target_currency="USA",
        id_column="donor_code",
        use_source_codes=True,
        value_column="D",
        to_current=True,
    )

    # Calculate the percentage deviation
    deviations = abs((test_df["value"] - test_df["A"]) / test_df["A"])

    # Filter out rows where A is NaN to avoid unnecessary comparisons
    mask = test_df["A"].notna() & (deviations >= tolerance)
    failing_rows = test_df[mask]

    # Focus on donor codes under 20000
    failing_rows = failing_rows.loc[lambda d: d.donor_code < 20000]

    # Assert that no rows exceed the tolerance
    assert failing_rows.empty, (
        f"Deviation exceeded {tolerance*100:.2f}% in the following "
        f"donors:\n"
        f"{failing_rows.donor_code.unique()}"
    )


def test_from_lcu(tolerance=0.01):

    # Perform the adjustment to current currency
    test_df = oecd_dac_deflate(
        data=df,
        base_year=2022,
        source_currency="LCU",
        target_currency="USA",
        id_column="donor_code",
        use_source_codes=True,
        value_column="N",
    )

    # Calculate the percentage deviation
    deviations = abs((test_df["value"] - test_df["D"]) / test_df["D"])

    # Filter out rows where A is NaN to avoid unnecessary comparisons
    mask = test_df["A"].notna() & (deviations >= tolerance)
    failing_rows = test_df[mask]

    # Focus on donor codes under 20000
    failing_rows = failing_rows.loc[lambda d: d.donor_code < 20000]

    # Assert that no rows exceed the tolerance
    assert failing_rows.empty, (
        f"Deviation exceeded {tolerance*100:.2f}% in the following "
        f"donors:\n"
        f"{failing_rows.donor_code.unique()}"
    )
