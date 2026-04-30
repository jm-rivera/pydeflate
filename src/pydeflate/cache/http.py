"""HTTP-level cache for World Bank wbgapi requests.

wbgapi 1.0.14 has no session-replacement hook (it calls ``requests.get``
directly), so the only reliable integration point is ``install_cache`` /
``uninstall_cache`` wrapped in a context manager — works inside
``ThreadPoolExecutor`` because ``requests`` reads the installed backend at
call time. ``disable_cache("http")`` flips ``_HTTP_DISABLED`` to make the
context manager a no-op.
"""

from __future__ import annotations

import contextlib
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import requests_cache

from pydeflate.cache.config import (
    http_cache_dir,
    register_cache_dir_change_listener,
)

_BACKEND = "filesystem"
_EXPIRE_AFTER = 86_400
_ALLOWABLE_CODES = (200,)
_MATCH_HEADERS = False

_CACHED_SESSION: requests_cache.CachedSession | None = None
_HTTP_DISABLED: bool = False


def _session_kwargs(cache_name: Path) -> dict:
    return {
        "cache_name": str(cache_name),
        "backend": _BACKEND,
        "expire_after": _EXPIRE_AFTER,
        "allowable_codes": _ALLOWABLE_CODES,
        "match_headers": _MATCH_HEADERS,
    }


def get_cached_session() -> requests_cache.CachedSession:
    """Return the process-level filesystem-backed ``CachedSession`` singleton."""
    global _CACHED_SESSION
    if _CACHED_SESSION is None:
        _CACHED_SESSION = requests_cache.CachedSession(
            **_session_kwargs(http_cache_dir() / "wb")
        )
    return _CACHED_SESSION


def _reset_cached_session() -> None:
    global _CACHED_SESSION
    _CACHED_SESSION = None
    # Defensive uninstall — handles the case where the ctx-mgr was active
    # when the cache root changed. uninstall_cache raises RuntimeError when
    # no cache is installed.
    with contextlib.suppress(RuntimeError):
        requests_cache.uninstall_cache()


@contextmanager
def wbgapi_cached_session() -> Generator[None, None, None]:
    """Install the HTTP cache for the enclosed block (no-op when disabled)."""
    if _HTTP_DISABLED:
        yield
        return

    requests_cache.install_cache(**_session_kwargs(http_cache_dir() / "wb"))
    try:
        yield
    finally:
        requests_cache.uninstall_cache()


register_cache_dir_change_listener(_reset_cached_session)
