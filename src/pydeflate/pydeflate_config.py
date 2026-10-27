from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from pathlib import Path

DATA_DIR_ENV = "PYDEFLATE_DATA_DIR"

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_SETTINGS_DIR = _PACKAGE_ROOT / "pydeflate" / "settings"
_TEST_DATA_DIR = _PACKAGE_ROOT / "tests" / "test_files"


def get_data_dir() -> Path:
    """Return the directory where pydeflate caches data files.

    Equivalent to ``pydeflate.cache.get_cache_root()``; the latter is the
    canonical name.
    """
    from pydeflate.cache.config import get_cache_root

    return get_cache_root()


def set_data_dir(path: str | Path) -> Path:
    """Override the pydeflate data directory for the current process.

    Equivalent to ``pydeflate.cache.set_cache_root(path)``; the latter is
    the canonical name.
    """
    from pydeflate.cache.config import set_cache_root

    return set_cache_root(path)


def reset_data_dir() -> None:
    """Reset any process-level overrides and fall back to defaults.

    Equivalent to ``pydeflate.cache.reset_cache_root()``; the latter is
    the canonical name.
    """
    from pydeflate.cache.config import reset_cache_root

    reset_cache_root()


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
    """Attach a console handler to a logger and set it to INFO.

    Deprecated: pydeflate leaves logging configuration to the application.
    Use ``logging.basicConfig()`` and
    ``logging.getLogger("pydeflate").setLevel(...)`` instead. Removed in 3.0.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger.

    """
    warnings.warn(
        "pydeflate.setup_logger is deprecated and will be removed in pydeflate "
        "3.0. Configure logging in your application, for example with "
        "logging.basicConfig() and logging.getLogger('pydeflate').setLevel().",
        DeprecationWarning,
        stacklevel=2,
    )
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


def __getattr__(name: str) -> logging.Logger:
    # A module-level ``logger`` would shadow this hook, so none may be defined.
    if name == "logger":
        warnings.warn(
            "pydeflate.pydeflate_config.logger is deprecated and will be removed "
            "in pydeflate 3.0. Use logging.getLogger('pydeflate').",
            DeprecationWarning,
            stacklevel=2,
        )
        return logging.getLogger("pydeflate")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def set_pydeflate_path(path: str | Path) -> Path:
    """Set the path to the data folder (public API)."""

    return set_data_dir(path)
