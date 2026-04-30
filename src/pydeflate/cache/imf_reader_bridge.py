"""Co-locate imf_reader's cache under pydeflate's cache root.

imf-reader 1.5+ exposes a public cache surface (``set_cache_dir``,
``clear_cache``, ``enable_cache``, ``disable_cache``) that mirrors pydeflate's.
We point it at ``<pydeflate root>/imf_reader`` so a single
``set_pydeflate_path()`` (or ``set_cache_root()``) call moves both caches in
lockstep, and ``pydeflate.cache.clear/enable_cache/disable_cache(scope='all')``
fans out to imf_reader.
"""

from __future__ import annotations

from pathlib import Path

from imf_reader import cache as _imf_cache

from pydeflate.cache.config import (
    imf_reader_cache_dir,
    register_cache_dir_change_listener,
)

# Last target we successfully passed to imf_reader; doubles as the
# "have we synced at all yet?" guard for the listener.
_synced_path: Path | None = None


def ensure_synced() -> None:
    """Point imf_reader's cache root at ``<pydeflate root>/imf_reader``.

    No-op when already pointed at the current target — safe to call on every
    request path.
    """
    global _synced_path
    target = imf_reader_cache_dir()
    if _synced_path == target:
        return
    _imf_cache.set_cache_dir(target)
    _synced_path = target


def _on_pydeflate_root_change() -> None:
    # Skip until first explicit sync — otherwise reset_cache_root() in a test
    # fixture would create the pydeflate root before any code path needs it.
    if _synced_path is not None:
        ensure_synced()


def clear_imf_reader_cache() -> None:
    ensure_synced()
    _imf_cache.clear_cache()


def enable_imf_reader_cache() -> None:
    _imf_cache.enable_cache()


def disable_imf_reader_cache() -> None:
    _imf_cache.disable_cache()


register_cache_dir_change_listener(_on_pydeflate_root_change)
