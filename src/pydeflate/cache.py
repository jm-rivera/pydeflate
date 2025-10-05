from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

from filelock import FileLock

from pydeflate.pydeflate_config import get_data_dir

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


@dataclass(frozen=True)
class CacheEntry:
    """Describe a cacheable dataset."""

    key: str
    filename: str
    fetcher: Callable[[Path], None]
    ttl_days: int = 30
    version: str | None = None


@dataclass(frozen=True)
class CacheRecord:
    key: str
    path: Path
    downloaded_at: datetime
    ttl_days: int
    version: str | None


class CacheError(RuntimeError):
    pass


class CacheManager:
    """Handle cached datasets stored under the pydeflate data directory."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_data_dir()).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.base_dir / "manifest.json"
        self._lock = FileLock(str(self.base_dir / ".cache.lock"))
        self._manifest: Dict[str, dict] = self._load_manifest()

    # ------------------------------------------------------------------
    def ensure(self, entry: CacheEntry, *, refresh: bool = False) -> Path:
        """Return a local path for the given entry, downloading when needed."""

        with self._lock:
            record = self._manifest.get(entry.key)
            path = self.base_dir / entry.filename

            if not refresh and record and path.exists():
                if not self._is_stale(record, entry):
                    return path

            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = Path(f"{path}.tmp-{os.getpid()}")
            try:
                entry.fetcher(tmp_path)
                tmp_path.replace(path)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)

            self._manifest[entry.key] = {
                "filename": entry.filename,
                "downloaded_at": datetime.now(timezone.utc).strftime(ISO_FORMAT),
                "ttl_days": entry.ttl_days,
                "version": entry.version,
            }
            self._save_manifest()
            return path

    # ------------------------------------------------------------------
    def list_records(self) -> Iterable[CacheRecord]:
        for key, payload in self._manifest.items():
            path = self.base_dir / payload["filename"]
            yield CacheRecord(
                key=key,
                path=path,
                downloaded_at=datetime.strptime(payload["downloaded_at"], ISO_FORMAT),
                ttl_days=payload["ttl_days"],
                version=payload.get("version"),
            )

    # ------------------------------------------------------------------
    def clear(self, key: str | None = None) -> None:
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
    def _is_stale(self, record: dict, entry: CacheEntry) -> bool:
        version_changed = entry.version is not None and entry.version != record.get(
            "version"
        )
        downloaded = datetime.strptime(record["downloaded_at"], ISO_FORMAT)
        age = datetime.now(timezone.utc) - downloaded
        ttl = timedelta(days=entry.ttl_days)
        return version_changed or age > ttl

    # ------------------------------------------------------------------
    def _load_manifest(self) -> Dict[str, dict]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text())
        except json.JSONDecodeError:
            return {}

    # ------------------------------------------------------------------
    def _save_manifest(self) -> None:
        payload = json.dumps(self._manifest, indent=2)
        self.manifest_path.write_text(payload)


_CACHE_MANAGER: Optional[CacheManager] = None


def cache_manager() -> CacheManager:
    global _CACHE_MANAGER
    base_dir = get_data_dir().resolve()
    if _CACHE_MANAGER is None or _CACHE_MANAGER.base_dir != base_dir:
        _CACHE_MANAGER = CacheManager(base_dir)
    return _CACHE_MANAGER
