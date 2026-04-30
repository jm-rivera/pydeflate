"""Tests for pydeflate's cache subsystem."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

import pydeflate
from pydeflate.cache import (
    ISO_FORMAT,
    BulkCacheManager,
    CacheEntry,
    CacheError,
    CacheManager,
    CacheRecord,
    bulk_cache_dir,
    bulk_cache_manager,
    cache_manager,
    clear,
    disable_cache,
    enable_cache,
    entries,
    get_cache_root,
    http_cache_dir,
    invalidate,
    path,
    register_cache_dir_change_listener,
    reset_cache_root,
    set_cache_root,
    size,
)
from pydeflate.cache.manager import _HOSTNAME, _tmp_path
from pydeflate.pydeflate_config import reset_data_dir, set_data_dir

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset the cache-root override, singletons, and listener list around each test.

    The listener list is snapshot-and-restored so tests that register extra
    listeners don't accumulate them across the suite (each reset_cache_root()
    call would otherwise call an ever-growing list of test lambdas).

    Also flips the pydeflate logger to ``propagate=True`` for the test duration
    so pytest's ``caplog`` fixture can capture warnings emitted from the
    package (production logger sets ``propagate=False``).
    """
    import pydeflate.cache.config as _cfg

    pkg_logger = logging.getLogger("pydeflate")
    saved_propagate = pkg_logger.propagate
    pkg_logger.propagate = True

    saved_listeners = list(_cfg._CACHE_DIR_LISTENERS)
    reset_cache_root()
    try:
        yield
    finally:
        reset_cache_root()
        _cfg._CACHE_DIR_LISTENERS[:] = saved_listeners
        pkg_logger.propagate = saved_propagate
        # Reset the per-scope enable/disable state so tests don't bleed into
        # each other through the module-level _SCOPE_ENABLED dict.
        try:
            from pydeflate.cache.api import enable_cache

            enable_cache("all")
        except ImportError:
            pass


# ---------------------------------------------------------------------------
# Original 5 tests (preserved exactly — BL2)
# ---------------------------------------------------------------------------


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
    stale_time = datetime.now(UTC) - timedelta(days=2)
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
    with pytest.warns(DeprecationWarning, match="cache_manager"):
        mgr = cache_manager()
    assert mgr.base_dir == tmp_path
    reset_data_dir()


# ---------------------------------------------------------------------------
# Slice A tests — config / listener bus / version segmentation
# ---------------------------------------------------------------------------


def test_set_cache_root_override(tmp_path):
    """set_cache_root() makes get_cache_root() return that path."""
    set_cache_root(tmp_path)
    assert get_cache_root() == tmp_path


def test_set_cache_root_fires_listener(tmp_path):
    """Registered listeners are called when the cache root changes."""
    calls = []
    register_cache_dir_change_listener(lambda: calls.append(1))

    set_cache_root(tmp_path)
    assert calls == [1]

    reset_cache_root()
    assert len(calls) == 2


def test_default_cache_root_is_version_segmented():
    """The platformdirs default ends with the package version."""
    root = get_cache_root()
    assert root.name == pydeflate.__version__


def test_env_var_bypasses_version_segmentation(monkeypatch, tmp_path):
    """PYDEFLATE_DATA_DIR bypasses version segmentation."""
    monkeypatch.setenv("PYDEFLATE_DATA_DIR", str(tmp_path))
    root = get_cache_root()
    assert root == tmp_path
    assert root.name != pydeflate.__version__


def test_set_data_dir_forwards_to_set_cache_root(tmp_path):
    """set_data_dir() is a thin forwarder to set_cache_root()."""
    set_data_dir(tmp_path)
    assert get_cache_root() == tmp_path


# ---------------------------------------------------------------------------
# Slice B tests — BulkCacheManager + manager.py
# ---------------------------------------------------------------------------


def test_atomic_manifest_write_recovers_from_truncation(tmp_path, caplog):
    """Corrupt manifest → warning + fresh start + fresh download."""
    # Write broken JSON before instantiation.
    (tmp_path / "manifest.json").write_text("not-json")

    with caplog.at_level(logging.WARNING, logger="pydeflate"):
        mgr = BulkCacheManager(tmp_path)

    assert any("Failed to load manifest" in r.message for r in caplog.records)
    assert mgr._manifest == {}

    def fetch(p):
        p.write_text("hello")

    entry = CacheEntry("k", "k.txt", fetch)
    mgr.ensure(entry)
    assert (tmp_path / "k.txt").exists()
    # The new manifest must be valid JSON.
    data = json.loads((tmp_path / "manifest.json").read_text())
    assert "k" in data


def test_tmp_path_uses_hostname_and_pid():
    """_tmp_path returns a path containing hostname and PID."""
    result = _tmp_path(Path("/x/y.parquet"))
    assert result.name == f"y.parquet.tmp-{_HOSTNAME}-{os.getpid()}"


def test_tmp_path_with_suffix():
    """_tmp_path with a suffix appends it after the pid."""
    result = _tmp_path(Path("/x/y.parquet"), suffix="retry")
    assert result.name == f"y.parquet.tmp-{_HOSTNAME}-{os.getpid()}.retry"


def test_sweep_old_tmp_files_removes_24h_orphans(tmp_path):
    """Orphaned *.tmp-* files older than 24 h are swept on manager init."""
    from pydeflate.cache.manager import _TMP_SWEEP_MAX_AGE_SECONDS

    old_tmp = tmp_path / "foo.parquet.tmp-host-123"
    old_tmp.write_text("orphan")
    old_mtime = os.path.getmtime(old_tmp) - _TMP_SWEEP_MAX_AGE_SECONDS - 60
    os.utime(old_tmp, (old_mtime, old_mtime))

    BulkCacheManager(tmp_path)

    assert not old_tmp.exists()


def test_sweep_leaves_recent_tmp_files(tmp_path):
    """Recent *.tmp-* files (< 24 h old) are NOT swept."""
    recent_tmp = tmp_path / "bar.parquet.tmp-host-999"
    recent_tmp.write_text("in-progress")

    BulkCacheManager(tmp_path)

    assert recent_tmp.exists()


def test_lru_eviction_drops_oldest_when_over_keep_n(tmp_path):
    """LRU eviction removes the oldest entries when keep_n is exceeded."""
    mgr = BulkCacheManager(tmp_path, keep_n=2)

    # Populate 4 entries with descending downloaded_at (most recent first).
    base_time = datetime.now(UTC) - timedelta(days=10)
    for i in range(4):
        key = f"entry_{i}"
        filename = f"entry_{i}.parquet"
        (tmp_path / filename).write_text(f"data_{i}")
        age = timedelta(days=i)  # i=0 newest, i=3 oldest
        mgr._manifest[key] = {
            "filename": filename,
            "downloaded_at": (base_time - age).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "ttl_days": 30,
            "version": None,
        }
    mgr._save_manifest()

    # Trigger eviction directly — startup maintenance is gated to once per
    # base_dir per process, so re-instantiating against the same tmp_path
    # doesn't re-fire it.
    with mgr._lock:
        mgr._evict_lru()

    assert len(mgr._manifest) == 2
    # The two oldest (i=2, i=3) should be evicted.
    assert "entry_2" not in mgr._manifest
    assert "entry_3" not in mgr._manifest
    assert not (tmp_path / "entry_2.parquet").exists()
    assert not (tmp_path / "entry_3.parquet").exists()


def test_concurrent_ensure_locks_dedup_downloads(tmp_path):
    """Concurrent ensure() calls for the same key download exactly once."""
    call_count = 0

    def fetch(path):
        nonlocal call_count
        call_count += 1
        path.write_text("data")

    mgr = BulkCacheManager(tmp_path)
    entry = CacheEntry("concurrent", "concurrent.txt", fetch)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(mgr.ensure, entry) for _ in range(4)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    assert call_count == 1


def test_atomic_write_failure_leaves_no_orphan(tmp_path):
    """If the fetcher raises, no tmp file or canonical file is left behind."""

    def bad_fetch(path):
        path.write_bytes(b"partial")
        raise OSError("disk full")

    mgr = BulkCacheManager(tmp_path)
    entry = CacheEntry("fail", "fail.parquet", bad_fetch)

    with pytest.raises(OSError):
        mgr.ensure(entry)

    # No tmp files.
    assert list(tmp_path.glob("*.tmp-*")) == []
    # No canonical file either.
    assert not (tmp_path / "fail.parquet").exists()


def test_fetcher_retry_on_integrity_failure(tmp_path):
    """integrity_check raising on first attempt triggers a retry."""
    import pyarrow

    fetch_count = 0
    integrity_call_count = 0

    def fetch(path):
        nonlocal fetch_count
        fetch_count += 1
        path.write_text("data")

    def integrity_check(path):
        nonlocal integrity_call_count
        integrity_call_count += 1
        if integrity_call_count == 1:
            raise pyarrow.ArrowInvalid("bad first time")

    entry = CacheEntry(
        "retry_ok", "retry_ok.parquet", fetch, integrity_check=integrity_check
    )
    mgr = BulkCacheManager(tmp_path)
    result = mgr.ensure(entry)

    assert fetch_count == 2
    assert result.exists()


def test_fetcher_retry_double_failure_raises_cache_error(tmp_path):
    """If integrity_check raises both times, CacheError is raised."""
    import pyarrow

    def fetch(path):
        path.write_text("bad")

    def always_bad(path):
        raise pyarrow.ArrowInvalid("always corrupt")

    entry = CacheEntry(
        "double_fail", "double_fail.parquet", fetch, integrity_check=always_bad
    )
    mgr = BulkCacheManager(tmp_path)

    with pytest.raises(CacheError) as exc_info:
        mgr.ensure(entry)

    assert exc_info.value.cache_path == str(tmp_path)


def test_list_records_populates_size_age_scope(tmp_path):
    """list_records() yields CacheRecord with size_bytes, age_days, scope."""

    def fetch(path):
        path.write_bytes(b"x" * 100)

    mgr = BulkCacheManager(tmp_path)
    entry = CacheEntry("rec", "rec.parquet", fetch)
    mgr.ensure(entry)

    records = list(mgr.list_records())
    assert len(records) == 1
    r = records[0]
    assert isinstance(r, CacheRecord)
    assert r.size_bytes == 100
    assert r.age_days >= 0.0
    assert r.scope == "bulk"


def test_legacy_layout_migration_moves_parquets(tmp_path, caplog):
    """Legacy flat-layout parquets are moved to the versioned bulk dir on first call."""
    import pydeflate.cache.config as _cfg
    from pydeflate.cache.config import _PACKAGE_VERSION, _auto_migrate_once

    # Use a test-controlled platformdirs root via monkeypatching.
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    fake_parquet = legacy_root / "fake.parquet"
    fake_parquet.write_bytes(b"parquet")

    # Point the versioned root to a sub-dir of tmp_path.
    versioned_root = tmp_path / "versioned" / _PACKAGE_VERSION
    versioned_root.mkdir(parents=True)

    # Capture original state to restore after test.
    orig_migrated = _cfg._AUTO_MIGRATED
    orig_override = _cfg._cache_root_override

    try:
        _cfg._AUTO_MIGRATED = False
        _cfg._cache_root_override = None

        with (
            patch(
                "pydeflate.cache.config.user_cache_path",
                return_value=legacy_root,
            ),
            patch(
                "pydeflate.cache.config.get_cache_root",
                return_value=versioned_root,
            ),
            caplog.at_level(logging.INFO, logger="pydeflate"),
        ):
            _auto_migrate_once()
    finally:
        _cfg._AUTO_MIGRATED = orig_migrated
        _cfg._cache_root_override = orig_override

    assert (versioned_root / "bulk" / "fake.parquet").exists()
    assert not fake_parquet.exists()
    assert any("Migrated" in r.message for r in caplog.records)


def test_cache_manager_alias_legacy_root(tmp_path):
    """CacheManager is a BulkCacheManager subclass rooted at get_cache_root()."""
    set_cache_root(tmp_path)

    assert issubclass(CacheManager, BulkCacheManager)
    with pytest.warns(DeprecationWarning, match="cache_manager"):
        legacy_dir = cache_manager().base_dir
    assert legacy_dir == get_cache_root()
    assert bulk_cache_manager().base_dir == get_cache_root() / "bulk"


def test_skip_cache_path_when_bulk_disabled(tmp_path):
    """When bulk cache is disabled, fetcher is invoked every call."""
    fetch_count = 0

    def fetch(path):
        nonlocal fetch_count
        fetch_count += 1
        path.write_text("data")

    mgr = BulkCacheManager(tmp_path)
    entry = CacheEntry("skip", "skip.parquet", fetch)

    disable_cache("bulk")
    try:
        mgr.ensure(entry)
        mgr.ensure(entry)
        assert fetch_count == 2

        enable_cache("bulk")
        mgr.ensure(entry)
        mgr.ensure(entry)
        assert fetch_count == 3  # only one fresh fetch after re-enable
    finally:
        enable_cache("bulk")


# ---------------------------------------------------------------------------
# Slice D tests — public API surface (cache/api.py)
# ---------------------------------------------------------------------------


def test_path_returns_scope_dirs(tmp_path):
    """path() returns the correct directory for each scope."""
    set_cache_root(tmp_path)
    assert path("all") == get_cache_root()
    assert path("bulk") == bulk_cache_dir()
    assert path("http") == http_cache_dir()


def test_path_validates_scope():
    """path() raises ValueError for an unknown scope."""
    with pytest.raises(ValueError):
        path("bogus")  # type: ignore[arg-type]


def test_entries_empty_cache_returns_empty_lists(tmp_path):
    """entries() returns {'bulk': [], 'http': []} on a fresh root."""
    set_cache_root(tmp_path)
    result = entries()
    assert result == {"bulk": [], "http": []}


def test_entries_after_ensure_populates_bulk(tmp_path):
    """entries()['bulk'] has one record after a single ensure()."""
    set_cache_root(tmp_path)

    def fetch(p: Path) -> None:
        p.write_bytes(b"x" * 50)

    entry = CacheEntry("imf_weo", "imf_weo.parquet", fetch)
    bulk_cache_manager().ensure(entry)

    result = entries()
    assert len(result["bulk"]) == 1
    r = result["bulk"][0]
    assert isinstance(r, CacheRecord)
    assert r.scope == "bulk"
    assert r.size_bytes > 0


def test_entries_http_scope_always_empty(tmp_path):
    """entries()['http'] is always [] even when the http dir has files."""
    set_cache_root(tmp_path)
    # Write a fake file into the http cache dir.
    http_dir = http_cache_dir()
    http_dir.mkdir(parents=True, exist_ok=True)
    (http_dir / "abc123.cache").write_text("fake response")

    result = entries()
    assert result["http"] == []


def test_size_per_scope(tmp_path):
    """size() returns non-zero for bulk after an ensure and >= 0 for http."""
    set_cache_root(tmp_path)

    def fetch(p: Path) -> None:
        p.write_bytes(b"y" * 200)

    entry = CacheEntry("world_bank", "world_bank.parquet", fetch)
    bulk_cache_manager().ensure(entry)

    result = size()
    assert result["bulk"] > 0
    assert result["http"] >= 0


def test_clear_bulk_only_does_not_touch_http(tmp_path):
    """clear('bulk') removes bulk parquets but leaves the http dir intact."""
    set_cache_root(tmp_path)

    def fetch(p: Path) -> None:
        p.write_bytes(b"data")

    entry = CacheEntry("dac_stats", "dac_stats.parquet", fetch)
    bulk_cache_manager().ensure(entry)

    # Place a fake file in the http cache dir.
    http_dir = http_cache_dir()
    http_file = http_dir / "response.cache"
    http_file.write_text("cached http response")

    clear("bulk")

    # No parquets remain in the bulk dir.
    parquets = list(bulk_cache_dir().glob("*.parquet"))
    assert parquets == []
    # The http file is untouched.
    assert http_file.exists()


def test_clear_returns_dict_keyed_by_scope(tmp_path):
    """clear('all') returns a dict with both scope keys and int values."""
    set_cache_root(tmp_path)
    result = clear("all")
    assert set(result.keys()) == {"bulk", "http"}
    assert all(isinstance(v, int) for v in result.values())


def test_invalidate_removes_single_bulk_entry(tmp_path):
    """invalidate('imf_weo') removes only the imf_weo entry."""
    set_cache_root(tmp_path)

    def fetch(p: Path) -> None:
        p.write_bytes(b"data")

    mgr = bulk_cache_manager()
    mgr.ensure(CacheEntry("imf_weo", "imf_weo.parquet", fetch))
    mgr.ensure(CacheEntry("dac_stats", "dac_stats.parquet", fetch))

    invalidate("imf_weo")

    assert "imf_weo" not in mgr._manifest
    assert "dac_stats" in mgr._manifest


def test_invalidate_unknown_key_raises_valueerror(tmp_path):
    """invalidate() with an unknown key raises ValueError listing known keys."""
    set_cache_root(tmp_path)
    with pytest.raises(ValueError, match="Unknown cache key") as exc_info:
        invalidate("not_a_real_key")

    assert "imf_weo" in str(exc_info.value)


def test_enable_disable_cache_toggles_state():
    """disable_cache / enable_cache correctly toggle is_scope_enabled."""
    from pydeflate.cache.api import is_scope_enabled

    disable_cache("bulk")
    assert is_scope_enabled("bulk") is False

    enable_cache("all")
    assert is_scope_enabled("bulk") is True
    assert is_scope_enabled("http") is True


# ---------------------------------------------------------------------------
# Slice E tests — set_pydeflate_path listener semantics (F7)
# ---------------------------------------------------------------------------


def test_set_pydeflate_path_invalidates_singleton(tmp_path):
    """set_pydeflate_path() resets the cache singleton so the next call picks
    up the new root — verifies F7's listener semantics via the public API."""
    from pydeflate import set_pydeflate_path

    # set_pydeflate_path → set_cache_root creates the directory; no pre-mkdir needed.
    set_pydeflate_path(tmp_path / "a")
    with pytest.warns(DeprecationWarning, match="cache_manager"):
        dir_a = cache_manager().base_dir

    set_pydeflate_path(tmp_path / "b")
    with pytest.warns(DeprecationWarning, match="cache_manager"):
        dir_b = cache_manager().base_dir

    assert dir_a != dir_b


# ---------------------------------------------------------------------------
# ArrowException umbrella catch tests
# ---------------------------------------------------------------------------


def test_fetcher_retry_on_arrow_io_error(tmp_path):
    """integrity_check raising ArrowIOError on first attempt triggers a retry."""
    import pyarrow

    fetch_count = 0
    integrity_call_count = 0

    def fetch(path):
        nonlocal fetch_count
        fetch_count += 1
        path.write_text("data")

    def integrity_check(path):
        nonlocal integrity_call_count
        integrity_call_count += 1
        if integrity_call_count == 1:
            raise pyarrow.ArrowIOError("simulated I/O")

    entry = CacheEntry(
        "retry_arrow_io",
        "retry_arrow_io.parquet",
        fetch,
        integrity_check=integrity_check,
    )
    mgr = BulkCacheManager(tmp_path)
    result = mgr.ensure(entry)

    assert fetch_count == 2
    assert result.exists()


# ---------------------------------------------------------------------------
# _clear_http raw-file sweep tests
# ---------------------------------------------------------------------------


def test_clear_http_removes_raw_files(tmp_path):
    """clear('http') removes raw files that were not written by requests-cache."""
    set_cache_root(tmp_path)

    # Write a stub raw file directly into the http cache dir.
    http_dir = http_cache_dir()
    http_dir.mkdir(parents=True, exist_ok=True)
    stray = http_dir / "stray.bin"
    stray.write_bytes(b"x")

    result = clear("http")

    assert not stray.exists()
    assert result["http"] >= 1


# ---------------------------------------------------------------------------
# Regression tests for cache-management coherence (P1/P2/P3)
# ---------------------------------------------------------------------------


def test_public_api_sees_source_writes(tmp_path):
    """Files written via bulk_cache_manager() (sources' path) are visible to
    entries()/clear()/invalidate() — guards against the API and source readers
    drifting onto different cache roots."""
    set_cache_root(tmp_path)

    def fetch(p: Path) -> None:
        p.write_bytes(b"payload")

    # Sources call bulk_cache_manager().ensure(...).
    entry = CacheEntry("imf_weo", "imf_weo.parquet", fetch)
    bulk_cache_manager().ensure(entry)

    # Public API must see it.
    result = entries()
    assert len(result["bulk"]) == 1
    assert result["bulk"][0].key == "imf_weo"

    # And clearing must actually remove the file on disk.
    clear("bulk")
    assert not (bulk_cache_dir() / "imf_weo.parquet").exists()
    assert entries()["bulk"] == []


def test_legacy_migration_preserves_manifest_records(tmp_path, caplog):
    """_auto_migrate_once moves the legacy manifest into the bulk dir so
    migrated parquets keep their cache records (no spurious re-download, and
    entries() reports them)."""
    import pydeflate.cache.config as _cfg
    from pydeflate.cache.config import _PACKAGE_VERSION, _auto_migrate_once

    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    (legacy_root / "imf_weo.parquet").write_bytes(b"parquet")
    legacy_manifest_payload = {
        "imf_weo": {
            "filename": "imf_weo.parquet",
            "downloaded_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "ttl_days": 60,
            "version": "3",
        }
    }
    (legacy_root / "manifest.json").write_text(json.dumps(legacy_manifest_payload))

    versioned_root = tmp_path / "versioned" / _PACKAGE_VERSION
    versioned_root.mkdir(parents=True)

    orig_migrated = _cfg._AUTO_MIGRATED
    orig_override = _cfg._cache_root_override

    try:
        _cfg._AUTO_MIGRATED = False
        _cfg._cache_root_override = None

        with (
            patch(
                "pydeflate.cache.config.user_cache_path",
                return_value=legacy_root,
            ),
            patch(
                "pydeflate.cache.config.get_cache_root",
                return_value=versioned_root,
            ),
            caplog.at_level(logging.INFO, logger="pydeflate"),
        ):
            _auto_migrate_once()
    finally:
        _cfg._AUTO_MIGRATED = orig_migrated
        _cfg._cache_root_override = orig_override

    new_manifest = versioned_root / "bulk" / "manifest.json"
    assert new_manifest.exists()
    migrated = json.loads(new_manifest.read_text())
    assert migrated == legacy_manifest_payload
    # Legacy manifest is gone (renamed, not copied).
    assert not (legacy_root / "manifest.json").exists()


def test_legacy_migration_does_not_clobber_existing_manifest(tmp_path):
    """If the new bulk dir already has a manifest, the legacy manifest is
    discarded rather than overwriting user data."""
    import pydeflate.cache.config as _cfg
    from pydeflate.cache.config import _PACKAGE_VERSION, _auto_migrate_once

    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    (legacy_root / "old.parquet").write_bytes(b"parquet")
    (legacy_root / "manifest.json").write_text('{"old": {"filename": "old.parquet"}}')

    versioned_root = tmp_path / "versioned" / _PACKAGE_VERSION
    new_bulk = versioned_root / "bulk"
    new_bulk.mkdir(parents=True)
    existing = '{"new": {"filename": "new.parquet"}}'
    (new_bulk / "manifest.json").write_text(existing)

    orig_migrated = _cfg._AUTO_MIGRATED
    orig_override = _cfg._cache_root_override

    try:
        _cfg._AUTO_MIGRATED = False
        _cfg._cache_root_override = None
        with (
            patch("pydeflate.cache.config.user_cache_path", return_value=legacy_root),
            patch("pydeflate.cache.config.get_cache_root", return_value=versioned_root),
        ):
            _auto_migrate_once()
    finally:
        _cfg._AUTO_MIGRATED = orig_migrated
        _cfg._cache_root_override = orig_override

    # Existing manifest preserved verbatim.
    assert (new_bulk / "manifest.json").read_text() == existing
    # Legacy manifest cleaned up.
    assert not (legacy_root / "manifest.json").exists()


def test_cache_manager_emits_deprecation_warning(tmp_path):
    """cache_manager() warns callers and steers them to bulk_cache_manager()."""
    set_cache_root(tmp_path)
    with pytest.warns(DeprecationWarning, match="bulk_cache_manager"):
        cache_manager()


def test_keep_n_enforced_after_each_ensure(tmp_path):
    """ensure() runs LRU eviction after every new manifest write — a long-
    lived process must not retain entries past keep_n until the next manager
    rebuild."""

    def fetch(p: Path) -> None:
        p.write_bytes(b"data")

    mgr = BulkCacheManager(tmp_path, keep_n=2)

    for i in range(5):
        # Distinct keys + distinct filenames so each call adds a new entry.
        mgr.ensure(CacheEntry(f"k{i}", f"k{i}.parquet", fetch))

    assert len(mgr._manifest) == 2
    # Only the two newest survive on disk.
    surviving_files = {p.name for p in tmp_path.glob("k*.parquet")}
    assert surviving_files == {"k3.parquet", "k4.parquet"}
    assert {"k3", "k4"} == set(mgr._manifest.keys())
