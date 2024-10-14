import pandas as pd

from pydeflate.sources.imf import _clean_columns


def test_clean_columns():
    # Create a sample dataframe with original IMF column names
    df = pd.DataFrame(
        {
            "REF_AREA_CODE": ["USA", "GBR"],
            "REF_AREA_LABEL": ["United States", "United Kingdom"],
            "LASTACTUALDATE": ["2020-12-31", "2021-12-31"],
            "TIME_PERIOD": [2020, 2021],
            "OBS_VALUE": [100, 200],
        }
    )

    # Expected column names after renaming
    expected_columns = [
        "entity_code",
        "entity",
        "estimates_start_after",
        "year",
        "value",
    ]

    # Call _clean_columns
    result = _clean_columns(df)

    # Assert the columns are renamed correctly
    assert list(result.columns) == expected_columns
