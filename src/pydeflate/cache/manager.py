"""BulkCacheManager — hardened on-disk cache for pydeflate's parquet datasets."""

from __future__ import annotations

import json
import logging
import os
import socket
import time
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import filelock
import pyarrow

from pydeflate.cache.config import (
    bulk_cache_dir,
    register_cache_dir_change_listener,
)
from pydeflate.cache.types import CacheEntry, CacheRecord
from pydeflate.exceptions import CacheError

logger = logging.getLogger("pydeflate")

_HOSTNAME: str = socket.gethostname()
_TMP_SWEEP_MAX_AGE_SECONDS: int = 86_400  # 24 hours

# Reads use fromisoformat() which accepts both this and the legacy
# microsecond format kept as ``cache.ISO_FORMAT`` for back-compat.
_WRITE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# Tracks base_dirs already swept this process — startup maintenance is
# expensive (directory walk + LRU sort) and need only run once per dir.
_STARTUP_MAINTENANCE_DONE: set[Path] = set()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tmp_path(path: Path, suffix: str = "") -> Path:
    """Return an NFS-safe tmp path for *path* (hostname+pid in suffix)."""
    tail = f".{suffix}" if suffix else ""
    return Path(f"{path}.tmp-{_HOSTNAME}-{os.getpid()}{tail}")


def _sweep_old_tmp_files(base_dir: Path) -> None:
    """Remove ``*.tmp-*`` orphans older than 24h (recovers from SIGKILL mid-fetch)."""
    cutoff = time.time() - _TMP_SWEEP_MAX_AGE_SECONDS
    for tmp in base_dir.glob("*.tmp-*"):
        try:
            if tmp.stat().st_mtime < cutoff:
                tmp.unlink(missing_ok=True)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# BulkCacheManager
# ---------------------------------------------------------------------------


class BulkCacheManager:
    """Manage cached parquet datasets stored under a single directory.

    Attributes:
        base_dir: Root directory for this manager's files.
        keep_n: Maximum number of entries to keep after LRU eviction.
        manifest_path: Path to the JSON manifest.
        lock_path: Path to the FileLock file.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        *,
        keep_n: int = 5,
    ) -> None:
        resolved = base_dir if base_dir is not None else bulk_cache_dir()
        self.base_dir = resolved.resolve()
        self.keep_n = keep_n
        self.manifest_path = self.base_dir / "manifest.json"
        self.lock_path = self.base_dir / ".cache.lock"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = filelock.FileLock(str(self.lock_path), timeout=1200)

        self._manifest: dict[str, dict] = self._load_manifest()

        # Sweep + LRU eviction is once-per-base_dir-per-process; subsequent
        # PydeflateContext or singleton-rebuild instances skip the rescan.
        if self.base_dir not in _STARTUP_MAINTENANCE_DONE:
            _STARTUP_MAINTENANCE_DONE.add(self.base_dir)
            try:
                with self._lock.acquire(timeout=0):
                    _sweep_old_tmp_files(self.base_dir)
                    self._evict_lru()
            except (OSError, filelock.Timeout):
                pass

    def ensure(self, entry: CacheEntry, *, refresh: bool = False) -> Path:
        """Return a local path for *entry*, downloading when stale or missing.

        Raises:
            CacheError: If two consecutive fetch attempts both fail integrity
                checks.
        """
        from pydeflate.cache.api import is_scope_enabled

        path = self.base_dir / entry.filename

        # Hot-path fast-read: cache hits don't acquire the FileLock. The
        # manifest is mutated only under-lock so a stale dict read at worst
        # forces a redundant lock acquisition below.
        if not refresh and is_scope_enabled("bulk"):
            record = self._manifest.get(entry.key)
            if record and path.exists() and not self._is_stale(record, entry):
                return path

        with self._lock:
            if not is_scope_enabled("bulk"):
                # Skip-cache path: fetch directly every call, no manifest write.
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = _tmp_path(path)
                try:
                    entry.fetcher(tmp)
                    tmp.replace(path)
                finally:
                    tmp.unlink(missing_ok=True)
                return path

            record = self._manifest.get(entry.key)
            if (
                not refresh
                and record
                and path.exists()
                and not self._is_stale(record, entry)
            ):
                return path

            path.parent.mkdir(parents=True, exist_ok=True)
            fetched_path = self._fetch_with_retry(entry, path)

            self._manifest[entry.key] = {
                "filename": entry.filename,
                "downloaded_at": datetime.now(UTC).strftime(_WRITE_FORMAT),
                "ttl_days": entry.ttl_days,
                "version": entry.version,
            }
            self._save_manifest()
            # Enforce keep_n in long-lived processes too — startup-only
            # eviction lets the cache grow unbounded between manager rebuilds.
            self._evict_lru()
            return fetched_path

    # ------------------------------------------------------------------
    def list_records(self) -> Iterable[CacheRecord]:
        """Yield a ``CacheRecord`` for each entry in the manifest."""
        now = datetime.now(UTC)
        for key, payload in self._manifest.items():
            path = self.base_dir / payload["filename"]
            try:
                size_bytes = path.stat().st_size
            except OSError:
                size_bytes = 0
            downloaded = datetime.fromisoformat(payload["downloaded_at"])
            age_days = (now - downloaded).total_seconds() / 86_400
            yield CacheRecord(
                key=key,
                path=path,
                size_bytes=size_bytes,
                age_days=age_days,
                version=payload.get("version"),
                scope="bulk",
            )

    # ------------------------------------------------------------------
    def clear(self, key: str | None = None) -> None:
        """Remove cached files; pass *key* for one entry or ``None`` for all."""
        with self._lock:
            if key is None:
                for payload in self._manifest.values():
                    (self.base_dir / payload["filename"]).unlink(missing_ok=True)
                self._manifest = {}
            else:
                payload = self._manifest.pop(key, None)
                if payload:
                    (self.base_dir / payload["filename"]).unlink(missing_ok=True)
            self._save_manifest()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_stale(self, record: dict, entry: CacheEntry) -> bool:
        version_changed = entry.version is not None and entry.version != record.get(
            "version"
        )
        downloaded = datetime.fromisoformat(record["downloaded_at"])
        age = datetime.now(UTC) - downloaded
        ttl = timedelta(days=entry.ttl_days)
        return version_changed or age > ttl

    def _load_manifest(self) -> dict[str, dict]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to load manifest at %s: %s; starting fresh.",
                self.manifest_path,
                exc,
            )
            return {}

    def _save_manifest(self) -> None:
        """Atomically persist ``self._manifest`` (tmp + replace)."""
        tmp = _tmp_path(self.manifest_path)
        try:
            tmp.write_text(json.dumps(self._manifest, indent=2))
            tmp.replace(self.manifest_path)
        finally:
            tmp.unlink(missing_ok=True)

    def _fetch_with_retry(self, entry: CacheEntry, path: Path) -> Path:
        """Fetch *entry* atomically; retry once if ``integrity_check`` fails.

        Custom ``integrity_check`` callables should raise
        ``pyarrow.ArrowException`` or ``OSError`` to signal corruption;
        anything else propagates directly without retry.
        """
        first_exc: Exception | None = None

        for attempt, suffix in enumerate(("", "retry")):
            tmp = _tmp_path(path, suffix=suffix)
            try:
                entry.fetcher(tmp)
                if entry.integrity_check is not None:
                    entry.integrity_check(tmp)
                tmp.replace(path)
                return path
            except (pyarrow.ArrowException, OSError) as exc:
                if entry.integrity_check is None:
                    # No integrity check — re-raise immediately without retry.
                    raise
                if attempt == 0:
                    first_exc = exc
                    continue
                # Second failure — give up.
                raise CacheError(
                    f"Fetch failed twice for {entry.key!r}: {exc}",
                    cache_path=str(self.base_dir),
                ) from first_exc
            finally:
                # Always clean up: harmless no-op when replace() already moved it.
                tmp.unlink(missing_ok=True)

        # Should be unreachable, but keeps the type-checker happy.
        raise CacheError(
            f"Fetch failed for {entry.key!r}",
            cache_path=str(self.base_dir),
        )

    def _evict_lru(self) -> None:
        """Drop oldest entries until ``len(manifest) <= keep_n`` (call under lock)."""
        if len(self._manifest) <= self.keep_n:
            return

        # Sort by downloaded_at ascending (oldest first).
        def _sort_key(item: tuple[str, dict]) -> datetime:
            try:
                return datetime.fromisoformat(item[1]["downloaded_at"])
            except (KeyError, ValueError):
                return datetime.min.replace(tzinfo=UTC)

        ordered = sorted(self._manifest.items(), key=_sort_key)
        to_evict = ordered[: len(ordered) - self.keep_n]

        for key, payload in to_evict:
            (self.base_dir / payload["filename"]).unlink(missing_ok=True)
            del self._manifest[key]

        self._save_manifest()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_BULK_CACHE_MANAGER: BulkCacheManager | None = None


def bulk_cache_manager() -> BulkCacheManager:
    """Return the singleton ``BulkCacheManager`` rooted at ``bulk_cache_dir()``."""
    global _BULK_CACHE_MANAGER
    if _BULK_CACHE_MANAGER is None:
        _BULK_CACHE_MANAGER = BulkCacheManager()
    return _BULK_CACHE_MANAGER


def _reset_bulk_cache_manager() -> None:
    global _BULK_CACHE_MANAGER
    _BULK_CACHE_MANAGER = None


register_cache_dir_change_listener(_reset_bulk_cache_manager)
