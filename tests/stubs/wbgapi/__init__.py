"""Minimal stub of the wbgapi package for tests."""
from types import SimpleNamespace

import pandas as pd


def _dataframe(*args, **kwargs):
    # The real implementation returns a pandas DataFrame. For tests we can
    # return an empty frame because the download logic is monkeypatched.
    return pd.DataFrame()


data = SimpleNamespace(DataFrame=_dataframe)
