from pathlib import Path

import pandas as pd
import pytest

from pydeflate.sources import dac, imf, world_bank


@pytest.fixture(autouse=True)
def stub_country(monkeypatch):
    mapping = {
        "United States": ("USA",),
        "Canada": ("CAN",),
        "Donor": ("DON",),
    }

    class DummyCountry:
        def get_iso3_country_code_fuzzy(self, value):
            return mapping.get(value, (value[:3].upper(),))

    monkeypatch.setattr("pydeflate.sources.common.Country", lambda: DummyCountry())


def _imf_sample_frame():
    rows = []
    for concept, values in {
        "NGDPD": [10.0, 12.0],
        "NGDP": [15.0, 18.0],
        "NGDP_D": [98.0, 100.0],
        "PCPI": [99.0, 101.0],
        "PCPIE": [100.0, 102.0],
    }.items():
        for year, value in zip([2021, 2022], values):
            rows.append(
                {
                    "CONCEPT_CODE": concept,
                    "OBS_VALUE": value,
                    "SCALE_CODE": 1,
                    "REF_AREA_CODE": "USA",
                    "REF_AREA_LABEL": "United States",
                    "LASTACTUALDATE": "2024-01-01",
                    "TIME_PERIOD": year,
                }
            )
    return pd.DataFrame(rows)


def test_download_weo_generates_parquet(monkeypatch, tmp_path):
    monkeypatch.setattr(imf.weo, "fetch_data", _imf_sample_frame)
    output = tmp_path / "weo.parquet"

    imf._download_weo(output)

    df = pd.read_parquet(output)
    assert {"pydeflate_iso3", "pydeflate_NGDP_D", "pydeflate_EXCHANGE"}.issubset(
        df.columns
    )


def _world_bank_indicator(name: str) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "year": [2021, 2022],
            "entity_code": ["USA", "CAN"],
            "entity": ["United States", "Canada"],
            name: [100.0, 105.0],
        }
    )
    return data.set_index(["year", "entity_code", "entity"])


def test_download_world_bank_dataset(monkeypatch, tmp_path):
    def fake_parallel(indicators):
        return [_world_bank_indicator(code) for code in indicators.values()]

    monkeypatch.setattr(world_bank, "_parallel_download_indicators", fake_parallel)
    output = tmp_path / "wb.parquet"

    world_bank._download_wb_dataset(world_bank._INDICATORS, output)
    df = pd.read_parquet(output)
    assert "pydeflate_iso3" in df.columns
    assert df["pydeflate_iso3"].isin(["USA", "CAN"]).all()


def test_download_world_bank_dataset_with_ppp(monkeypatch, tmp_path):
    def fake_parallel(indicators):
        return [_world_bank_indicator(code) for code in indicators.values()]

    monkeypatch.setattr(world_bank, "_parallel_download_indicators", fake_parallel)
    output = tmp_path / "wb_lcu_ppp.parquet"

    world_bank._download_wb_dataset(
        world_bank._INDICATORS_LCU_PPP, output, add_ppp_exchange=True
    )
    df = pd.read_parquet(output)
    assert "pydeflate_iso3" in df.columns
    assert "PPP" in df["pydeflate_iso3"].unique()


def _dac_sample_frame():
    return pd.DataFrame(
        {
            "year": [2021, 2021, 2021, 2022, 2022, 2022],
            "unit_multiplier": [1, 1, 1, 1, 1, 1],
            "aidtype_code": [1010, 1010, 1010, 1010, 1010, 1010],
            "flows_code": [1140, 1140, 1140, 1140, 1140, 1140],
            "donor_code": [1, 1, 1, 1, 1, 1],
            "donor_name": ["Donor", "Donor", "Donor", "Donor", "Donor", "Donor"],
            "amounttype_code": ["A", "N", "D", "A", "N", "D"],
            "value": [100.0, 110.0, 100.0, 100.0, 120.0, 95.0],
        }
    )


def test_download_dac_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(dac, "download_dac1", lambda **_: _dac_sample_frame())
    monkeypatch.setattr(
        dac,
        "_pivot_amount_type",
        lambda df: pd.DataFrame(
            {
                "year": [2021, 2022],
                "donor_code": [1, 1],
                "donor_name": ["Donor", "Donor"],
                "A": [100.0, 110.0],
                "N": [100.0, 120.0],
                "D": [100.0, 105.0],
            }
        ),
    )
    output = tmp_path / "dac.parquet"

    dac._download_dac(output)
    df = pd.read_parquet(output)
    assert "pydeflate_DAC_DEFLATOR" in df.columns
    assert "pydeflate_iso3" in df.columns


def test_pivot_amount_type_creates_columns():
    pivoted = dac._pivot_amount_type(_dac_sample_frame())
    assert {"A", "N", "D"}.issubset(pivoted.columns)


def test_world_bank_read_functions(monkeypatch, tmp_path):
    data = pd.DataFrame({"pydeflate_iso3": ["USA"], "value": [1]})

    class DummyCache:
        def __init__(self, path: Path):
            self.path = path

        def ensure(self, entry, refresh=False):
            data.to_parquet(self.path)
            return self.path

    cache_path = tmp_path / "wb.parquet"
    dummy = DummyCache(cache_path)
    monkeypatch.setattr(world_bank, "cache_manager", lambda: dummy)

    df = world_bank.read_wb(update=True)
    assert not df.empty

    dummy_lcu = DummyCache(tmp_path / "wb_lcu.parquet")
    monkeypatch.setattr(world_bank, "cache_manager", lambda: dummy_lcu)
    df = world_bank.read_wb_lcu_ppp(update=False)
    assert not df.empty

    dummy_usd = DummyCache(tmp_path / "wb_usd.parquet")
    monkeypatch.setattr(world_bank, "cache_manager", lambda: dummy_usd)
    df = world_bank.read_wb_usd_ppp(update=False)
    assert not df.empty
