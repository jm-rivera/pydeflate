"""Tests for the HTTP-level cache (cache/http.py) and World Bank wiring.

Slice C — F8 coverage.
"""

from __future__ import annotations

import pytest
import responses as resp

import pydeflate.cache.http as http_mod
from pydeflate.cache.config import set_cache_root
from pydeflate.cache.http import (
    _reset_cached_session,
    get_cached_session,
    wbgapi_cached_session,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_http_state(tmp_path):
    """Reset the HTTP-cache singleton and flag before / after each test.

    Also points the cache root at *tmp_path* so tests don't touch
    production cache directories.
    """
    set_cache_root(tmp_path)
    http_mod._HTTP_DISABLED = False
    _reset_cached_session()
    try:
        yield
    finally:
        http_mod._HTTP_DISABLED = False
        _reset_cached_session()


# ---------------------------------------------------------------------------
# Unit tests for get_cached_session / _reset_cached_session
# ---------------------------------------------------------------------------


def test_get_cached_session_returns_cachedsession_under_http_dir(tmp_path):
    """get_cached_session() returns a CachedSession rooted at http_cache_dir()."""
    import requests_cache

    from pydeflate.cache.config import http_cache_dir

    session = get_cached_session()

    assert isinstance(session, requests_cache.CachedSession)
    # The cache_name should be a string path under the http sub-dir.
    assert str(http_cache_dir() / "wb") in session.cache.cache_name


def test_set_cache_root_resets_cached_session(tmp_path):
    """Changing the cache root invalidates the CachedSession singleton."""
    # Hold a strong reference: comparing id() across a GC point is unreliable
    # — CPython will happily reuse the old object's memory address for the
    # next allocation (observed on 3.14).
    session_before = get_cached_session()

    # Change the cache root — the listener bus fires _reset_cached_session.
    other_path = tmp_path / "other"
    set_cache_root(other_path)

    session_after = get_cached_session()

    assert session_before is not session_after


# ---------------------------------------------------------------------------
# Integration tests: wbgapi wiring
#
# Strategy: use `responses` to intercept HTTP at the adapter layer.
# requests_cache.install_cache (active inside wbgapi_cached_session) caches
# at the session layer.  On a cache hit the second call never reaches the
# adapter, so responses.calls stays at 1.
# ---------------------------------------------------------------------------


def _make_wb_response() -> dict:
    """Minimal World Bank API JSON payload for a single indicator/country."""
    return {
        "page": 1,
        "pages": 1,
        "per_page": 50,
        "total": 1,
        "sourceid": "2",
        "lastupdated": "2024-01-01",
        "data": [
            {
                "indicator": {"id": "NY.GDP.DEFL.ZS", "value": "GDP deflator"},
                "country": {"id": "US", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2020",
                "value": 112.5,
                "unit": "",
                "obs_status": "",
                "decimal": 1,
            }
        ],
    }


_WB_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.DEFL.ZS"
    "?format=json&per_page=1000&page=1"
)


@resp.activate
def test_two_consecutive_wb_calls_share_one_roundtrip(tmp_path):
    """Two requests.get() calls to the WB endpoint hit the network once.

    Proves that ``wbgapi_cached_session()`` correctly installs a process-wide
    requests-cache so any ``requests`` consumer — including ``wbgapi`` itself,
    which uses the ``requests`` stack under the hood — gets transparent
    caching for the duration of the context.

    We exercise the cache via ``requests.get`` directly rather than calling
    ``wb.data.DataFrame(...)`` to keep the test focused on the HTTP layer
    (wbgapi's response parsing requires a richer mocked payload that would
    couple this test to wbgapi internals).
    """
    import requests

    resp.add(resp.GET, _WB_URL, json=_make_wb_response(), status=200)

    with wbgapi_cached_session():
        r1 = requests.get(_WB_URL, timeout=5)
        r2 = requests.get(_WB_URL, timeout=5)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(resp.calls) == 1, (
        f"Expected 1 network round-trip (cache hit on second call), "
        f"got {len(resp.calls)}"
    )


@resp.activate
def test_disable_cache_http_bypasses_caching(tmp_path):
    """When ``_HTTP_DISABLED`` is True, each requests.get goes to the network."""
    import requests

    resp.add(resp.GET, _WB_URL, json=_make_wb_response(), status=200)
    resp.add(resp.GET, _WB_URL, json=_make_wb_response(), status=200)

    http_mod._HTTP_DISABLED = True
    try:
        with wbgapi_cached_session():
            requests.get(_WB_URL, timeout=5)
            requests.get(_WB_URL, timeout=5)
    finally:
        http_mod._HTTP_DISABLED = False

    assert len(resp.calls) == 2, (
        f"Expected 2 network round-trips (cache disabled), got {len(resp.calls)}"
    )
