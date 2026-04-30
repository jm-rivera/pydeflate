"""pydeflate cache package — public surface mirrors oda-data 2.6 / oda-reader 1.6.

Legacy symbols (``CacheManager``, ``cache_manager``, ``CacheError``,
``ISO_FORMAT``) are re-exported for back-compat. New code should prefer
``bulk_cache_manager()`` and the scoped helpers (``path``, ``entries``,
``clear``, etc.).
"""

from __future__ import annotations

import warnings
from pathlib import Path

from pydeflate.cache.api import (
    clear,
    disable_cache,
    enable_cache,
    entries,
    invalidate,
    path,
    size,
)
from pydeflate.cache.config import (
    bulk_cache_dir,
    get_cache_root,
    http_cache_dir,
    register_cache_dir_change_listener,
    reset_cache_root,
    set_cache_root,
)
from pydeflate.cache.manager import BulkCacheManager, bulk_cache_manager
from pydeflate.cache.types import (
    CacheEntry,
    CacheRecord,
    Scope,
)

# Canonical home is pydeflate.exceptions; re-exported for back-compat.
from pydeflate.exceptions import CacheError

# Legacy format kept as a test seam (microsecond format).
# New writes use the shorter format without microseconds; reads use fromisoformat().
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


class CacheManager(BulkCacheManager):
    """Legacy alias rooted at ``get_cache_root()`` (no ``bulk`` segment).

    Preserves the v2.4 contract ``set_data_dir(tmp) → cache_manager().base_dir == tmp``.
    New code should use ``bulk_cache_manager()`` instead.
    """

    def __init__(self, base_dir: Path | None = None, *, keep_n: int = 5) -> None:
        if base_dir is None:
            base_dir = get_cache_root()
        super().__init__(base_dir=base_dir, keep_n=keep_n)


_CACHE_MANAGER: CacheManager | None = None


def cache_manager() -> CacheManager:
    """Return the legacy un-scoped ``CacheManager`` singleton.

    .. deprecated::
        Use :func:`bulk_cache_manager` instead. The legacy singleton is
        rooted at ``get_cache_root()`` (no ``bulk`` segment) and is not
        visible to ``entries()`` / ``clear()`` / ``invalidate()``; files
        written via this manager won't appear in the public cache API.
    """
    warnings.warn(
        "cache_manager() is deprecated and will be removed in a future "
        "release; use bulk_cache_manager() instead. The legacy un-scoped "
        "manager writes to a directory the public cache API "
        "(entries/clear/invalidate) does not inspect.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _CACHE_MANAGER
    if _CACHE_MANAGER is None:
        _CACHE_MANAGER = CacheManager()
    return _CACHE_MANAGER


def _reset_cache_manager() -> None:
    global _CACHE_MANAGER
    _CACHE_MANAGER = None


register_cache_dir_change_listener(_reset_cache_manager)


__all__ = [
    "BulkCacheManager",
    "CacheEntry",
    "CacheError",
    "CacheManager",
    "CacheRecord",
    "ISO_FORMAT",
    "Scope",
    "bulk_cache_dir",
    "bulk_cache_manager",
    "cache_manager",
    "clear",
    "disable_cache",
    "enable_cache",
    "entries",
    "get_cache_root",
    "http_cache_dir",
    "invalidate",
    "path",
    "register_cache_dir_change_listener",
    "reset_cache_root",
    "set_cache_root",
    "size",
]
