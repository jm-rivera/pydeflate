"""Public API surface for the pydeflate cache subsystem.

Scopes: ``"bulk"`` (parquet datasets), ``"http"`` (requests-cache backend
for World Bank), ``"all"`` (sentinel meaning every concrete scope).
"""

from __future__ import annotations

import logging
from pathlib import Path

import filelock

from pydeflate.cache.config import (
    bulk_cache_dir,
    get_cache_root,
    http_cache_dir,
)
from pydeflate.cache.types import CacheRecord, Scope, _validate_scope

logger = logging.getLogger("pydeflate")

_CANONICAL_BULK_KEYS: frozenset[str] = frozenset(
    {"imf_weo", "dac_stats", "world_bank", "world_bank_lcu_ppp", "world_bank_usd_ppp"}
)

# "all" is intentionally absent: it is an iteration sigil at the API boundary.
_SCOPE_ENABLED: dict[str, bool] = {"bulk": True, "http": True}


def _dir_size(directory: Path) -> int:
    """Sum of ``stat().st_size`` for every regular file under *directory*."""
    total = 0
    for item in directory.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            pass
    return total


def path(scope: Scope = "all") -> Path:
    """Return the on-disk path for *scope*.

    ``"all"`` resolves to the cache root; ``"bulk"`` / ``"http"`` to their
    sub-directory. Raises ``ValueError`` on unknown scopes.
    """
    _validate_scope(scope)
    if scope == "bulk":
        return bulk_cache_dir()
    if scope == "http":
        return http_cache_dir()
    return get_cache_root()


def entries() -> dict[Scope, list[CacheRecord]]:
    """Return cached records keyed by concrete scope.

    ``"http"`` is always empty — requests-cache uses opaque hash filenames;
    use ``pydeflate.cache.http.get_cached_session().cache`` for HTTP
    introspection.
    """
    from pydeflate.cache.manager import bulk_cache_manager

    return {"bulk": list(bulk_cache_manager().list_records()), "http": []}


def clear(scope: Scope = "all", *, blocking: bool = True) -> dict[Scope, int | None]:
    """Remove cached data for *scope*; return per-scope counts.

    With ``blocking=True`` (default) all values are ``int``. ``None`` only
    appears when ``blocking=False`` AND the scope's lock is held by another
    process.
    """
    _validate_scope(scope)

    result: dict[Scope, int | None] = {}
    scopes_to_clear: list[Scope] = (
        ["bulk", "http"] if scope == "all" else [scope]  # type: ignore[list-item]
    )

    for s in scopes_to_clear:
        if s == "bulk":
            result["bulk"] = _clear_bulk(blocking=blocking)
        else:
            result["http"] = _clear_http()

    if scope == "all":
        from pydeflate.cache.imf_reader_bridge import clear_imf_reader_cache

        clear_imf_reader_cache()

    return result


def _clear_bulk(*, blocking: bool) -> int | None:
    """Clear the bulk cache; return item count or ``None`` on lock contention."""
    from pydeflate.cache.manager import bulk_cache_manager

    mgr = bulk_cache_manager()

    if not blocking:
        try:
            with mgr._lock.acquire(timeout=0):
                count = len(mgr._manifest)
                mgr.clear()
                return count
        except filelock.Timeout:
            return None

    count = len(mgr._manifest)
    mgr.clear()
    return count


def _clear_http() -> int:
    """Clear the HTTP cache; return count of files actually removed.

    Calls requests-cache's own ``cache.clear()`` first, then sweeps any
    leftover raw files (e.g. files written outside requests-cache).
    """
    from pydeflate.cache.http import get_cached_session

    http_dir = http_cache_dir()
    if not http_dir.is_dir():
        return 0
    get_cached_session().cache.clear()
    count = 0
    for f in http_dir.rglob("*"):
        if not f.is_file():
            continue
        try:
            f.unlink()
            count += 1
        except OSError as e:
            logger.warning("clear_http: could not unlink %s: %s", f, e)
    return count


def size() -> dict[Scope, int]:
    """Return on-disk sizes in bytes, keyed by concrete scope.

    Returns:
        ``{"bulk": <bytes>, "http": <bytes>}``
    """
    return {
        "bulk": _dir_size(bulk_cache_dir()),
        "http": _dir_size(http_cache_dir()),
    }


def invalidate(key: str) -> None:
    """Remove a single bulk cache entry by key.

    Canonical keys: ``"imf_weo"``, ``"dac_stats"``, ``"world_bank"``,
    ``"world_bank_lcu_ppp"``, ``"world_bank_usd_ppp"``. Any current manifest
    key is also accepted. Raises ``ValueError`` for unknown keys.
    """
    from pydeflate.cache.manager import bulk_cache_manager

    mgr = bulk_cache_manager()
    known = _CANONICAL_BULK_KEYS | set(mgr._manifest.keys())
    if key not in known:
        raise ValueError(f"Unknown cache key {key!r}; known: {sorted(known)}")
    mgr.clear(key)


def enable_cache(scope: Scope = "all") -> None:
    """Enable caching for *scope* (rebuilds the HTTP session on the next use)."""
    _validate_scope(scope)
    _set_scope_enabled(scope, enabled=True)


def disable_cache(scope: Scope = "all") -> None:
    """Disable caching for *scope*.

    ``"bulk"`` makes ``ensure()`` bypass the manifest and re-fetch each call.
    ``"http"`` makes ``wbgapi_cached_session()`` a no-op until re-enabled.
    """
    _validate_scope(scope)
    _set_scope_enabled(scope, enabled=False)


def _set_scope_enabled(scope: Scope, *, enabled: bool) -> None:
    targets: list[str] = list(_SCOPE_ENABLED.keys()) if scope == "all" else [scope]
    for s in targets:
        _SCOPE_ENABLED[s] = enabled

    if scope in ("http", "all"):
        # Late import to avoid circular load at module import time.
        import pydeflate.cache.http as _http

        _http._HTTP_DISABLED = not enabled
        _http._reset_cached_session()

    if scope == "all":
        from pydeflate.cache.imf_reader_bridge import (
            disable_imf_reader_cache,
            enable_imf_reader_cache,
        )

        if enabled:
            enable_imf_reader_cache()
        else:
            disable_imf_reader_cache()


def is_scope_enabled(scope: str) -> bool:
    """Return whether caching is enabled for *scope* (internal helper)."""
    return _SCOPE_ENABLED.get(scope, True)
