"""Types for the pydeflate cache subsystem.

Scope taxonomy, CacheEntry, CacheRecord, and scope validation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args

Scope = Literal["all", "bulk", "http"]

_SCOPE_VALUES: tuple[str, ...] = get_args(Scope)


def _validate_scope(scope: object) -> Scope:
    """Raise ``ValueError`` if *scope* is not one of the allowed Scope literals."""
    if scope not in _SCOPE_VALUES:
        raise ValueError(
            f"Invalid scope {scope!r}; must be one of {list(_SCOPE_VALUES)}"
        )
    return scope  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """Describe a cacheable dataset.

    ``integrity_check`` runs against the tmp path after the fetcher writes
    but before the atomic replace; raising ``pyarrow.ArrowException`` or
    ``OSError`` from it triggers a single retry.
    """

    key: str
    filename: str
    fetcher: Callable[[Path], None]
    ttl_days: int = 30
    version: str | None = None
    integrity_check: Callable[[Path], None] | None = None


@dataclass(frozen=True, slots=True)
class CacheRecord:
    """Public observability record for a cached entry (oda-data 2.6 parity).

    ``size_bytes`` is raw bytes; users wanting MB compute ``size_bytes / 2**20``.
    ``version`` is ``str | None`` (oda-data uses ``str``) because pydeflate
    allows None-version entries.
    """

    key: str
    path: Path
    size_bytes: int
    age_days: float
    version: str | None
    scope: Scope
