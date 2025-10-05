from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path


from platformdirs import user_cache_dir


DATA_DIR_ENV = "PYDEFLATE_DATA_DIR"

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_SETTINGS_DIR = _PACKAGE_ROOT / "pydeflate" / "settings"
_TEST_DATA_DIR = _PACKAGE_ROOT / "tests" / "test_files"

_DATA_DIR_OVERRIDE: Path | None = None


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _default_data_dir() -> Path:
    env_value = os.environ.get(DATA_DIR_ENV)
    if env_value:
        return _ensure_dir(Path(env_value).expanduser().resolve())
    return _ensure_dir(Path(user_cache_dir("pydeflate", "pydeflate")))


def get_data_dir() -> Path:
    """Return the directory where pydeflate caches data files."""

    if _DATA_DIR_OVERRIDE is not None:
        return _ensure_dir(_DATA_DIR_OVERRIDE)
    return _default_data_dir()


def set_data_dir(path: str | Path) -> Path:
    """Override the pydeflate data directory for the current process."""

    global _DATA_DIR_OVERRIDE
    resolved = _ensure_dir(Path(path).expanduser().resolve())
    _DATA_DIR_OVERRIDE = resolved
    return resolved


def reset_data_dir() -> None:
    """Reset any process-level overrides and fall back to defaults."""

    global _DATA_DIR_OVERRIDE
    _DATA_DIR_OVERRIDE = None


@dataclass(frozen=True)
class _Paths:
    package: Path
    settings: Path
    test_data: Path

    @property
    def data(self) -> Path:
        return get_data_dir()

    @data.setter  # type: ignore[override]
    def data(self, value: Path | str) -> None:  # pragma: no cover - simple proxy
        set_data_dir(value)


PYDEFLATE_PATHS = _Paths(
    package=_PACKAGE_ROOT,
    settings=_SETTINGS_DIR,
    test_data=_TEST_DATA_DIR,
)


def setup_logger(name) -> logging.Logger:
    """Set up the logger.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger.

    """
    logger_ = logging.getLogger(name)
    logger_.setLevel(logging.INFO)

    # Only add handlers if the logger has none to avoid duplication
    if not logger_.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s:\n %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger_.addHandler(console_handler)
        logger_.propagate = False

    return logger_


logger = setup_logger("pydeflate")


def set_pydeflate_path(path: str | Path) -> Path:
    """Set the path to the data folder (public API)."""

    return set_data_dir(path)
