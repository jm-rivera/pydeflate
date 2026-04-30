"""Cache root resolution, override stack, and listener bus.

Single source of truth for where pydeflate caches data. Resolution priority:
``set_cache_root()`` override → ``PYDEFLATE_DATA_DIR`` env var → version-
segmented platformdirs default. Overrides bypass version segmentation.
"""

from __future__ import annotations

import importlib.metadata
import logging
import os
from collections.abc import Callable
from pathlib import Path

from platformdirs import user_cache_path

from pydeflate.pydeflate_config import DATA_DIR_ENV

logger = logging.getLogger("pydeflate")

try:
    _PACKAGE_VERSION: str = importlib.metadata.version("pydeflate")
except importlib.metadata.PackageNotFoundError:
    _PACKAGE_VERSION = "0.0.0"

_cache_root_override: Path | None = None
_CACHE_DIR_LISTENERS: list[Callable[[], None]] = []
_AUTO_MIGRATED: bool = False


def get_cache_root() -> Path:
    """Resolve the cache root.

    Priority: ``set_cache_root()`` override > ``PYDEFLATE_DATA_DIR`` env var >
    ``user_cache_path("pydeflate", "pydeflate") / __version__``. Auto-migrates
    a legacy flat layout once per process when using the platformdirs default.
    """
    if _cache_root_override is not None:
        root = _cache_root_override
        root.mkdir(parents=True, exist_ok=True)
        return root

    env_value = os.environ.get(DATA_DIR_ENV)
    if env_value:
        root = Path(env_value).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    root = user_cache_path("pydeflate", "pydeflate") / _PACKAGE_VERSION
    root.mkdir(parents=True, exist_ok=True)
    _auto_migrate_once()
    return root


def set_cache_root(path: str | Path) -> Path:
    """Set a custom cache root (precedence over env var and default)."""
    global _cache_root_override
    resolved = Path(path).expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    _cache_root_override = resolved
    _notify_cache_dir_changed()
    return resolved


def reset_cache_root() -> None:
    """Clear the override; fall back to env var or platformdirs default."""
    global _cache_root_override
    _cache_root_override = None
    _notify_cache_dir_changed()


def register_cache_dir_change_listener(callback: Callable[[], None]) -> None:
    """Register a zero-arg callback fired when the cache root changes.

    Idempotent against duplicate registrations — re-imports won't accumulate
    duplicate listeners.
    """
    if callback not in _CACHE_DIR_LISTENERS:
        _CACHE_DIR_LISTENERS.append(callback)


def _notify_cache_dir_changed() -> None:
    for cb in _CACHE_DIR_LISTENERS:
        cb()


def bulk_cache_dir() -> Path:
    """Return ``get_cache_root() / "bulk"``, creating it if needed."""
    d = get_cache_root() / "bulk"
    d.mkdir(parents=True, exist_ok=True)
    return d


def http_cache_dir() -> Path:
    """Return ``get_cache_root() / "http"``, creating it if needed."""
    d = get_cache_root() / "http"
    d.mkdir(parents=True, exist_ok=True)
    return d


def imf_reader_cache_dir() -> Path:
    """Return ``get_cache_root() / "imf_reader"`` (no mkdir; imf_reader owns I/O)."""
    return get_cache_root() / "imf_reader"


def _auto_migrate_once() -> None:
    """Best-effort move of legacy flat-layout parquets into the versioned bulk dir.

    Runs at most once per process. Skipped when an override or env-var is in
    effect (the user explicitly chose a path; we do not touch the platformdirs
    tree from under them). Failures downgrade to a WARNING.
    """
    global _AUTO_MIGRATED

    if _AUTO_MIGRATED:
        return

    # Set the guard BEFORE the body — the body calls get_cache_root() which
    # re-enters this function. Inverting the order would recurse unboundedly.
    _AUTO_MIGRATED = True

    if _cache_root_override is not None or os.environ.get(DATA_DIR_ENV):
        return

    legacy_root = user_cache_path("pydeflate", "pydeflate")
    if not legacy_root.exists():
        return

    parquets = list(legacy_root.glob("*.parquet"))
    if not parquets:
        return

    try:
        new_bulk = get_cache_root() / "bulk"
        new_bulk.mkdir(parents=True, exist_ok=True)
        moved = 0
        for src in parquets:
            dst = new_bulk / src.name
            src.rename(dst)
            moved += 1
        # Move the legacy manifest into the bulk dir so cache records survive
        # the migration; otherwise the next ensure() sees no record and re-
        # downloads, and entries() reports an empty cache.
        legacy_manifest = legacy_root / "manifest.json"
        if legacy_manifest.exists():
            new_manifest = new_bulk / "manifest.json"
            if new_manifest.exists():
                # Don't clobber a manifest the new manager already wrote.
                legacy_manifest.unlink(missing_ok=True)
            else:
                legacy_manifest.rename(new_manifest)
        logger.info(
            "Migrated %d cached parquet(s) from %s to %s.",
            moved,
            legacy_root,
            new_bulk,
        )
    except OSError as exc:
        logger.warning(
            "Failed to migrate legacy cache from %s: %s; continuing without migration.",
            legacy_root,
            exc,
        )
