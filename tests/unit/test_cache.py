import json
from datetime import datetime, timedelta, timezone

import pytest

from pydeflate.cache import CacheEntry, CacheManager, cache_manager
from pydeflate.cache import ISO_FORMAT
from pydeflate.pydeflate_config import reset_data_dir, set_data_dir


@pytest.fixture
def tmp_cache(tmp_path):
    mgr = CacheManager(tmp_path)
    return mgr


def test_cache_ensure_downloads_once(tmp_path):
    calls = []

    def fetch(path):
        calls.append(path)
        path.write_text("data")

    mgr = CacheManager(tmp_path)
    entry = CacheEntry("sample", "sample.txt", fetch, ttl_days=30)

    path = mgr.ensure(entry)
    assert path.read_text() == "data"
    assert len(calls) == 1

    mgr.ensure(entry)
    assert len(calls) == 1  # cached


def test_cache_refresh_on_ttl(tmp_path):
    calls = []

    def fetch(path):
        calls.append(path)
        path.write_text(str(len(calls)))

    mgr = CacheManager(tmp_path)
    entry = CacheEntry("stale", "stale.txt", fetch, ttl_days=1)

    mgr.ensure(entry)
    assert len(calls) == 1

    # Age the entry beyond TTL
    record = mgr._manifest[entry.key]
    stale_time = datetime.now(timezone.utc) - timedelta(days=2)
    record["downloaded_at"] = stale_time.strftime(ISO_FORMAT)
    mgr._save_manifest()

    mgr.ensure(entry)
    assert len(calls) == 2


def test_cache_refresh_on_version_change(tmp_path):
    calls = []

    def fetch(path):
        calls.append(path)
        path.write_text("version")

    mgr = CacheManager(tmp_path)
    entry_v1 = CacheEntry("versioned", "file.txt", fetch, ttl_days=10, version="v1")
    mgr.ensure(entry_v1)
    assert len(calls) == 1

    entry_v2 = CacheEntry("versioned", "file.txt", fetch, ttl_days=10, version="v2")
    mgr.ensure(entry_v2)
    assert len(calls) == 2


def test_cache_clear(tmp_path):
    def fetch(path):
        path.write_text("data")

    mgr = CacheManager(tmp_path)
    entry = CacheEntry("clear", "clear.txt", fetch)
    path = mgr.ensure(entry)
    assert path.exists()

    mgr.clear("clear")
    assert not path.exists()
    assert "clear" not in mgr._manifest

    mgr.ensure(entry)
    mgr.clear()
    assert len(mgr._manifest) == 0


def test_cache_manager_tracks_data_dir(tmp_path):
    reset_data_dir()
    set_data_dir(tmp_path)
    mgr = cache_manager()
    assert mgr.base_dir == tmp_path
    reset_data_dir()
