from collections import defaultdict

import pandas as pd

from pydeflate.core.schema import PydeflateSchema


def schema_types() -> dict:
    """
    Returns a dictionary of schema types. Invalid columns are assumed to be strings.
    By default, pyarrow types are used for all columns.

    Returns:
        dict: A dictionary mapping attribute names to their corresponding data types.

    """
    types = {
        PydeflateSchema.YEAR: "int16[pyarrow]",
        PydeflateSchema.PROVIDER_CODE: "int16[pyarrow]",
        PydeflateSchema.PROVIDER_NAME: "string[pyarrow]",
        PydeflateSchema.VALUE: "float64[pyarrow]",
        PydeflateSchema.USD_COMMITMENT: "float64[pyarrow]",
        PydeflateSchema.USD_DISBURSEMENT: "float64[pyarrow]",
        PydeflateSchema.EXCHANGE: "float64[pyarrow]",
        PydeflateSchema.DEFLATOR: "float64[pyarrow]",
        PydeflateSchema.AID_TYPE: "int32[pyarrow]",
        PydeflateSchema.AMOUNT_TYPE: "string[pyarrow]",
        PydeflateSchema.FLOWS: "int32[pyarrow]",
        PydeflateSchema.EXCHANGE_DEFLATOR: "float64[pyarrow]",
        PydeflateSchema.PRICE_DEFLATOR: "float64[pyarrow]",
    }

    return defaultdict(lambda: "string[pyarrow]", types)


def set_default_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Set the types of the columns in the dataframe.

    Args:
        df (pd.DataFrame): The input dataframe.

    Returns:
        pd.DataFrame: The dataframe with the types set.

    """
    default_types = schema_types()

    converted_types = {c: default_types[c] for c in df.columns}

    return df.astype(converted_types)
