import pytest

from pydeflate.pydeflate_config import (
    DATA_DIR_ENV,
    get_data_dir,
    reset_data_dir,
    set_data_dir,
)


@pytest.fixture(autouse=True)
def restore_data_dir(monkeypatch, tmp_path):
    # Slice A moved the platformdirs lookup into pydeflate.cache.config and
    # switched from user_cache_dir (str) to user_cache_path (Path).
    def fake_user_cache_path(appname: str, appauthor: str):
        from pathlib import Path

        return Path(tmp_path / "default-cache")

    monkeypatch.setattr("pydeflate.cache.config.user_cache_path", fake_user_cache_path)
    reset_data_dir()
    yield
    reset_data_dir()


def test_get_data_dir_uses_env(monkeypatch, tmp_path):
    target = tmp_path / "env-cache"
    monkeypatch.setenv(DATA_DIR_ENV, str(target))
    reset_data_dir()
    resolved = get_data_dir()
    assert resolved == target
    assert resolved.exists()


def test_set_data_dir_overrides(monkeypatch, tmp_path):
    target = tmp_path / "custom"
    set_data_dir(target)
    assert get_data_dir() == target

    reset_data_dir()
    assert get_data_dir() != target


def test_get_data_dir_creates_directory(tmp_path):
    set_data_dir(tmp_path / "nested" / "cache")
    dir_path = get_data_dir()
    assert dir_path.exists()
    assert dir_path.is_dir()


def test_reset_data_dir(monkeypatch, tmp_path):
    set_data_dir(tmp_path)
    reset_data_dir()
    default_dir = get_data_dir()
    assert default_dir != tmp_path
    assert default_dir.exists()
