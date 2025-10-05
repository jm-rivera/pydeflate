import contextlib
import importlib.machinery
import sys
import types
from pathlib import Path

import pandas as pd
import pytest


STUB_PATH = (Path(__file__).parent / "stubs").resolve()
if str(STUB_PATH) not in sys.path:
    sys.path.insert(0, str(STUB_PATH))


stub = types.ModuleType("wbgapi")
stub.data = types.SimpleNamespace(DataFrame=lambda *args, **kwargs: pd.DataFrame())
stub.__spec__ = importlib.machinery.ModuleSpec(name="wbgapi", loader=None)
sys.modules.setdefault("wbgapi", stub)


import builtins
import importlib


_real_import_module = importlib.import_module
_real_import = builtins.__import__


def _import_module(name, package=None):
    if name == "wbgapi":
        return sys.modules["wbgapi"]
    return _real_import_module(name, package)


def _import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "wbgapi":
        return sys.modules["wbgapi"]
    return _real_import(name, globals, locals, fromlist, level)


importlib.import_module = _import_module
builtins.__import__ = _import

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, reset_data_dir, set_data_dir
from pydeflate.sources.common import enforce_pyarrow_types

YEARS = [2021, 2022, 2023]
ENTITY_INFO = {
    "USA": {"iso": "USA", "code": "001"},
    "FRA": {"iso": "FRA", "code": "250"},
    "GBR": {"iso": "GBR", "code": "826"},
    "CAN": {"iso": "CAN", "code": "124"},
    "EUR": {"iso": "EUR", "code": "978"},
    "PPP": {"iso": "PPP", "code": "PPP"},
    "EUI": {"iso": "EUI", "code": "918"},
    "DAC": {"iso": "DAC", "code": "20001"},
}


def _series(mapping):
    def getter(entity, index):
        return mapping[entity][index]

    return getter


def _uniform(seq):
    def getter(entity, index):
        return seq[index]

    return getter


def _constant(value):
    def getter(entity, index):
        return value

    return getter


def _build_source_frame(entities, column_factories):
    records = []
    for entity in entities:
        info = ENTITY_INFO[entity]
        for idx, year in enumerate(YEARS):
            row = {
                "pydeflate_year": year,
                "pydeflate_entity_code": info["code"],
                "pydeflate_iso3": info["iso"],
            }
            for column, factory in column_factories.items():
                row[column] = factory(entity, idx)
            records.append(row)
    return enforce_pyarrow_types(pd.DataFrame.from_records(records))


@pytest.fixture(autouse=True)
def patch_data_dirs(tmp_path):
    data_dir = tmp_path / "pydeflate-data"
    set_data_dir(data_dir)
    yield
    reset_data_dir()


@pytest.fixture(scope="session")
def sample_source_frames():
    common_exchange_def = _uniform([96.0, 100.0, 104.0])

    imf_frames = _build_source_frame(
        ["USA", "FRA", "GBR", "CAN", "EUR"],
        {
            "pydeflate_NGDP_D": _series(
                {
                    "USA": [98.0, 100.0, 103.0],
                    "FRA": [95.0, 100.0, 108.0],
                    "GBR": [96.0, 100.0, 105.0],
                    "CAN": [97.0, 100.0, 104.0],
                    "EUR": [95.5, 100.0, 107.5],
                }
            ),
            "pydeflate_PCPI": _series(
                {
                    "USA": [99.0, 100.0, 102.0],
                    "FRA": [96.0, 100.0, 107.0],
                    "GBR": [97.0, 100.0, 104.0],
                    "CAN": [98.0, 100.0, 103.0],
                    "EUR": [96.5, 100.0, 107.5],
                }
            ),
            "pydeflate_PCPIE": _series(
                {
                    "USA": [99.5, 100.0, 102.5],
                    "FRA": [96.5, 100.0, 107.5],
                    "GBR": [97.5, 100.0, 104.5],
                    "CAN": [98.5, 100.0, 103.5],
                    "EUR": [97.0, 100.0, 108.0],
                }
            ),
            "pydeflate_EXCHANGE": _series(
                {
                    "USA": [1.0, 1.0, 1.0],
                    "FRA": [0.84, 0.85, 0.86],
                    "GBR": [0.73, 0.74, 0.75],
                    "CAN": [1.26, 1.27, 1.28],
                    "EUR": [0.9, 0.91, 0.92],
                }
            ),
            "pydeflate_EXCHANGE_D": common_exchange_def,
        },
    )

    wb_frames = _build_source_frame(
        ["USA", "FRA", "GBR", "CAN", "EUR"],
        {
            "pydeflate_NGDP_D": _series(
                {
                    "USA": [97.0, 100.0, 104.0],
                    "FRA": [94.0, 100.0, 107.0],
                    "GBR": [95.0, 100.0, 106.0],
                    "CAN": [96.0, 100.0, 105.0],
                    "EUR": [94.5, 100.0, 107.5],
                }
            ),
            "pydeflate_NGDP_DL": _series(
                {
                    "USA": [96.0, 100.0, 105.0],
                    "FRA": [93.0, 100.0, 108.0],
                    "GBR": [94.0, 100.0, 107.0],
                    "CAN": [95.0, 100.0, 106.0],
                    "EUR": [93.5, 100.0, 108.5],
                }
            ),
            "pydeflate_CPI": _series(
                {
                    "USA": [98.0, 100.0, 103.0],
                    "FRA": [95.0, 100.0, 106.0],
                    "GBR": [96.0, 100.0, 105.0],
                    "CAN": [97.0, 100.0, 104.0],
                    "EUR": [95.5, 100.0, 106.5],
                }
            ),
            "pydeflate_EXCHANGE": _series(
                {
                    "USA": [1.0, 1.0, 1.0],
                    "FRA": [0.83, 0.84, 0.85],
                    "GBR": [0.72, 0.73, 0.74],
                    "CAN": [1.25, 1.26, 1.27],
                    "EUR": [0.9, 0.91, 0.92],
                }
            ),
            "pydeflate_EXCHANGE_D": common_exchange_def,
        },
    )

    wb_ppp_frames = _build_source_frame(
        ["USA", "CAN", "PPP"],
        {
            "pydeflate_NGDP_D": _series(
                {
                    "USA": [100.0, 100.0, 100.0],
                    "CAN": [100.0, 100.0, 100.0],
                    "PPP": [100.0, 100.0, 100.0],
                }
            ),
            "pydeflate_NGDP_DL": _series(
                {
                    "USA": [100.0, 100.0, 100.0],
                    "CAN": [100.0, 100.0, 100.0],
                    "PPP": [100.0, 100.0, 100.0],
                }
            ),
            "pydeflate_EXCHANGE": _series(
                {
                    "USA": [1.0, 1.0, 1.0],
                    "CAN": [1.28, 1.27, 1.26],
                    "PPP": [1.1, 1.1, 1.1],
                }
            ),
            "pydeflate_EXCHANGE_D": _uniform([100.0, 100.0, 100.0]),
        },
    )

    dac_frames = _build_source_frame(
        ["USA", "GBR", "CAN", "EUI", "DAC"],
        {
            "pydeflate_NGDP_D": _series(
                {
                    "USA": [97.0, 100.0, 104.0],
                    "GBR": [96.0, 100.0, 105.0],
                    "CAN": [95.0, 100.0, 106.0],
                    "EUI": [98.5, 100.0, 103.0],
                    "DAC": [98.0, 100.0, 102.0],
                }
            ),
            "pydeflate_EXCHANGE": _series(
                {
                    "USA": [1.0, 1.0, 1.0],
                    "GBR": [0.72, 0.73, 0.74],
                    "CAN": [1.24, 1.25, 1.26],
                    "EUI": [0.9, 0.91, 0.92],
                    "DAC": [1.0, 1.0, 1.0],
                }
            ),
            "pydeflate_EXCHANGE_D": common_exchange_def,
            "pydeflate_DAC_DEFLATOR": _series(
                {
                    "USA": [97.0, 100.0, 104.0],
                    "GBR": [96.0, 100.0, 105.0],
                    "CAN": [95.0, 100.0, 106.0],
                    "EUI": [98.5, 100.0, 103.0],
                    "DAC": [98.0, 100.0, 102.0],
                }
            ),
        },
    )

    return {
        "imf": imf_frames,
        "world_bank": wb_frames,
        "world_bank_ppp": wb_ppp_frames,
        "dac": dac_frames,
    }


@pytest.fixture(autouse=True)
def mock_source_readers(sample_source_frames, monkeypatch):
    monkeypatch.setattr(
        "pydeflate.sources.imf.read_weo",
        lambda update=False: sample_source_frames["imf"],
    )
    monkeypatch.setattr(
        "pydeflate.core.source.read_weo",
        lambda update=False: sample_source_frames["imf"],
    )
    monkeypatch.setattr(
        "pydeflate.sources.world_bank.read_wb",
        lambda update=False: sample_source_frames["world_bank"],
    )
    monkeypatch.setattr(
        "pydeflate.core.source.read_wb",
        lambda update=False: sample_source_frames["world_bank"],
    )
    monkeypatch.setattr(
        "pydeflate.sources.world_bank.read_wb_lcu_ppp",
        lambda update=False: sample_source_frames["world_bank_ppp"],
    )
    monkeypatch.setattr(
        "pydeflate.sources.world_bank.read_wb_usd_ppp",
        lambda update=False: sample_source_frames["world_bank_ppp"],
    )
    monkeypatch.setattr(
        "pydeflate.core.source.read_wb_lcu_ppp",
        lambda update=False: sample_source_frames["world_bank_ppp"],
    )
    monkeypatch.setattr(
        "pydeflate.core.source.read_wb_usd_ppp",
        lambda update=False: sample_source_frames["world_bank_ppp"],
    )
    monkeypatch.setattr(
        "pydeflate.sources.dac.read_dac",
        lambda update=False: sample_source_frames["dac"],
    )
    monkeypatch.setattr(
        "pydeflate.core.source.read_dac",
        lambda update=False: sample_source_frames["dac"],
    )
    yield


@pytest.fixture
def sample_constant_price_frame():
    return pd.DataFrame(
        {
            "iso_code": ["USA", "USA", "FRA", "FRA"],
            "year": [2021, 2023, 2021, 2023],
            "value": [100.0, 150.0, 120.0, 180.0],
        }
    )


@pytest.fixture
def sample_source_code_frame():
    return pd.DataFrame(
        {
            "entity_code": ["001", "001", "826"],
            "year": [2021, 2022, 2022],
            "value": [1000.0, 1050.0, 500.0],
        }
    )


@pytest.fixture
def caplog_info(caplog):
    with caplog.at_level("INFO"):
        yield caplog


@contextlib.contextmanager
def swap_logger_level(logger, level):
    previous = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(previous)


@pytest.fixture
def enforce_info_logging():
    from pydeflate.pydeflate_config import logger

    with swap_logger_level(logger, level="INFO"):
        yield logger
