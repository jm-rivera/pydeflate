"""Context management for dependency injection.

This module provides a context-based approach to managing pydeflate's
configuration and cache. This eliminates global state and enables better
testability and parallel execution.

pydeflate does not configure logging. Its modules log through
``logging.getLogger(__name__)`` under the ``pydeflate`` logger, and the
application sets handlers and levels.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import threading
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import CodeType
from typing import Any

from pydeflate.cache import BulkCacheManager
from pydeflate.protocols import CacheManagerProtocol
from pydeflate.pydeflate_config import get_data_dir

# Frames in pydeflate's own package and in contextlib's module file are
# skipped when attributing the log_level deprecation, so the warning names the
# caller's file and line whether the value came through the dataclass,
# ``create``, ``pydeflate_session`` or ``temporary_context`` (the last two run
# inside ``contextlib``). The trailing separator keeps sibling directories such
# as ``pydeflate_extras`` out, and matching contextlib's file keeps third-party
# packages installed under the stdlib directory in view.
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep
_CONTEXTLIB_FILE = contextlib.__file__


def _is_internal_frame(code: CodeType) -> bool:
    """Whether a frame belongs to pydeflate's machinery rather than its caller.

    Dataclass-generated ``__init__`` methods report the filename ``<string>``.
    Matching on that filename together with the ``__init__`` name skips them,
    including a base ``__init__`` reached through ``super().__init__``, while a
    ``python -c`` caller's frame (named ``<module>``) stays visible.
    """
    filename = code.co_filename
    return (
        filename.startswith(_PACKAGE_DIR)
        or filename == _CONTEXTLIB_FILE
        or (filename == "<string>" and code.co_name == "__init__")
    )


@dataclass
class PydeflateContext:
    """Encapsulates all runtime configuration for pydeflate operations.

    This class holds the cache manager, data directory, and other runtime
    settings. Using a context object instead of global variables
    enables:
    - Multiple independent configurations in the same process
    - Better testability (mock the context instead of globals)
    - Thread-safe parallel operations
    - Clear dependency tracking

    Attributes:
        data_dir: Directory where deflator/exchange data is cached
        cache_manager: Manages cached datasets
        logger: Deprecated, removed in 3.0. Defaults to the shared
            ``logging.getLogger("pydeflate")``. pydeflate does not read it.
        log_level: Deprecated, removed in 3.0. Has no effect; passing a
            value emits a ``DeprecationWarning``. Configure the
            ``pydeflate`` logger in your application instead.
        enable_validation: Whether to validate data schemas (recommended: True)
        config: Additional configuration options
    """

    data_dir: Path
    cache_manager: CacheManagerProtocol | None = None
    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("pydeflate")
    )
    log_level: int | None = None
    enable_validation: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the cache manager and warn on the deprecated log_level."""
        if self.cache_manager is None:
            self.cache_manager = BulkCacheManager(self.data_dir)

        if self.log_level is not None:
            frame = sys._getframe()
            stacklevel = 1
            while frame.f_back is not None and _is_internal_frame(frame.f_code):
                frame = frame.f_back
                stacklevel += 1
            warnings.warn(
                "log_level is deprecated, has no effect, and will be removed in "
                "pydeflate 3.0. Configure the 'pydeflate' logger in your "
                "application, for example "
                "logging.getLogger('pydeflate').setLevel(logging.DEBUG).",
                DeprecationWarning,
                stacklevel=stacklevel,
            )

    @classmethod
    def create(
        cls,
        data_dir: str | Path | None = None,
        log_level: int | None = None,
        enable_validation: bool = True,
        **config,
    ) -> PydeflateContext:
        """Factory method to create a context with sensible defaults.

        Args:
            data_dir: Path to cache directory. If None, uses default from config.
            log_level: Deprecated, has no effect. Passing a value emits a
                ``DeprecationWarning``.
            enable_validation: Enable schema validation
            **config: Additional configuration options

        Returns:
            New PydeflateContext instance
        """
        data_dir = (
            get_data_dir()
            if data_dir is None
            else Path(data_dir).expanduser().resolve()
        )

        return cls(
            data_dir=data_dir,
            log_level=log_level,
            enable_validation=enable_validation,
            config=config,
        )


# Thread-local storage for default context
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
    log_level: int | None = None,
    enable_validation: bool = True,
    group_treatment: str | None = None,
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
        log_level: Deprecated, has no effect. Passing a value emits a
            ``DeprecationWarning``.
        enable_validation: Enable schema validation
        group_treatment: How to treat country groups ('source', 'fixed', 'dynamic')
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

    # Save and restore group registry state
    from pydeflate.groups import GroupTreatment as GT
    from pydeflate.groups import _registry

    previous_state = _registry.snapshot()

    try:
        if group_treatment is not None:
            _registry.default_treatment = GT(group_treatment)
        # Set as default for this thread
        set_default_context(context)
        yield context
    finally:
        # Restore group registry state
        _registry.restore(previous_state)
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
        **overrides: Configuration overrides (data_dir, enable_validation,
            config). A ``log_level`` override is deprecated and only warns.

    Yields:
        Temporary PydeflateContext with overrides applied
    """
    default = get_default_context()

    # Create new context with overrides
    config = default.config.copy()
    config.update(overrides.get("config", {}))

    temp_ctx = PydeflateContext.create(
        data_dir=overrides.get("data_dir", default.data_dir),
        log_level=overrides.get("log_level"),
        enable_validation=overrides.get("enable_validation", default.enable_validation),
        **config,
    )

    previous = get_default_context()
    try:
        set_default_context(temp_ctx)
        yield temp_ctx
    finally:
        set_default_context(previous)
