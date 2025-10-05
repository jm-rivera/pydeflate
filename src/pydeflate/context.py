"""Context management for dependency injection.

This module provides a context-based approach to managing pydeflate's
configuration, cache, and logging. This eliminates global state and
enables better testability and parallel execution.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

from pydeflate.cache import CacheManager
from pydeflate.pydeflate_config import get_data_dir


@dataclass
class PydeflateContext:
    """Encapsulates all runtime configuration for pydeflate operations.

    This class holds the cache manager, data directory, logger, and other
    runtime settings. Using a context object instead of global variables
    enables:
    - Multiple independent configurations in the same process
    - Better testability (mock the context instead of globals)
    - Thread-safe parallel operations
    - Clear dependency tracking

    Attributes:
        data_dir: Directory where deflator/exchange data is cached
        cache_manager: Manages cached datasets
        logger: Logger instance for this context
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_validation: Whether to validate data schemas (recommended: True)
        config: Additional configuration options
    """

    data_dir: Path
    cache_manager: CacheManager | None = None
    logger: logging.Logger | None = None
    log_level: int = logging.INFO
    enable_validation: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize cache manager and logger if not provided."""
        if self.cache_manager is None:
            self.cache_manager = CacheManager(self.data_dir)

        if self.logger is None:
            self.logger = self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create a logger for this context."""
        from pydeflate.pydeflate_config import setup_logger

        logger = setup_logger(f"pydeflate.{id(self)}")
        logger.setLevel(self.log_level)
        return logger

    @classmethod
    def create(
        cls,
        data_dir: str | Path | None = None,
        log_level: int = logging.INFO,
        enable_validation: bool = True,
        **config,
    ) -> PydeflateContext:
        """Factory method to create a context with sensible defaults.

        Args:
            data_dir: Path to cache directory. If None, uses default from config.
            log_level: Logging level for this context
            enable_validation: Enable schema validation
            **config: Additional configuration options

        Returns:
            New PydeflateContext instance
        """
        if data_dir is None:
            data_dir = get_data_dir()
        else:
            data_dir = Path(data_dir).expanduser().resolve()

        return cls(
            data_dir=data_dir,
            log_level=log_level,
            enable_validation=enable_validation,
            config=config,
        )


# Thread-local storage for default context
import threading

_thread_local = threading.local()


def get_default_context() -> PydeflateContext:
    """Get the default context for the current thread.

    If no context has been set, creates one with default settings.

    Returns:
        PydeflateContext for current thread
    """
    if not hasattr(_thread_local, "context"):
        _thread_local.context = PydeflateContext.create()
    return _thread_local.context


def set_default_context(context: PydeflateContext) -> None:
    """Set the default context for the current thread.

    Args:
        context: Context to use as default
    """
    _thread_local.context = context


@contextmanager
def pydeflate_session(
    data_dir: str | Path | None = None,
    log_level: int = logging.INFO,
    enable_validation: bool = True,
    **config,
) -> Generator[PydeflateContext, None, None]:
    """Context manager for pydeflate operations with custom configuration.

    This is the recommended way to use pydeflate when you need custom
    configuration. It ensures clean setup and teardown.

    Example:
        >>> from pydeflate.context import pydeflate_session
        >>> with pydeflate_session(data_dir="/tmp/my_cache") as ctx:
        ...     # Use ctx for deflation operations
        ...     result = imf_gdp_deflate(df, context=ctx, ...)

    Args:
        data_dir: Path to cache directory
        log_level: Logging level
        enable_validation: Enable schema validation
        **config: Additional configuration

    Yields:
        PydeflateContext configured with the given parameters
    """
    context = PydeflateContext.create(
        data_dir=data_dir,
        log_level=log_level,
        enable_validation=enable_validation,
        **config,
    )

    # Save previous default context
    previous_context = getattr(_thread_local, "context", None)

    try:
        # Set as default for this thread
        set_default_context(context)
        yield context
    finally:
        # Restore previous context
        if previous_context is not None:
            set_default_context(previous_context)
        elif hasattr(_thread_local, "context"):
            delattr(_thread_local, "context")


@contextmanager
def temporary_context(
    **overrides,
) -> Generator[PydeflateContext, None, None]:
    """Create a temporary context with specific overrides.

    This is useful for testing or temporarily changing configuration.

    Example:
        >>> from pydeflate.context import temporary_context
        >>> with temporary_context(enable_validation=False) as ctx:
        ...     # Validation disabled for this block
        ...     result = process_data(ctx=ctx)

    Args:
        **overrides: Configuration overrides (log_level, enable_validation, etc.)

    Yields:
        Temporary PydeflateContext with overrides applied
    """
    default = get_default_context()

    # Create new context with overrides
    config = default.config.copy()
    config.update(overrides.get("config", {}))

    temp_ctx = PydeflateContext.create(
        data_dir=overrides.get("data_dir", default.data_dir),
        log_level=overrides.get("log_level", default.log_level),
        enable_validation=overrides.get("enable_validation", default.enable_validation),
        **config,
    )

    previous = get_default_context()
    try:
        set_default_context(temp_ctx)
        yield temp_ctx
    finally:
        set_default_context(previous)
