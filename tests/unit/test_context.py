"""Tests for context management and dependency injection."""

import contextlib
import logging
import os
import warnings
from pathlib import Path

import pytest

import pydeflate.context
from pydeflate.context import (
    PydeflateContext,
    get_default_context,
    pydeflate_session,
    set_default_context,
    temporary_context,
)

# Each helper passes log_level and returns the file the warning must name.


def _construct_with_log_level(path):
    PydeflateContext(data_dir=path, log_level=logging.DEBUG)
    return __file__


def _create_with_log_level(path):
    PydeflateContext.create(data_dir=path, log_level=logging.DEBUG)
    return __file__


def _session_with_log_level(path):
    with pydeflate_session(data_dir=path, log_level=logging.DEBUG):
        pass
    return __file__


def _temporary_with_log_level(path):
    with temporary_context(log_level=logging.DEBUG):
        pass
    return __file__


class _ContextSubclass(PydeflateContext):
    def __init__(self, data_dir):
        super().__init__(data_dir=data_dir, log_level=logging.DEBUG)


def _subclass_with_log_level(path):
    _ContextSubclass(path)
    return __file__


def _library_call_from(filename):
    """Build a caller whose frames report ``filename``, like an installed library."""

    def call(path):
        source = (
            "def call(path):\n"
            "    PydeflateContext.create(data_dir=path, log_level=10)\n"
        )
        namespace = {"PydeflateContext": PydeflateContext}
        exec(compile(source, filename, "exec"), namespace)
        namespace["call"](path)
        return filename

    return call


# site-packages sits inside the stdlib directory on system Python, Docker and conda.
_site_packages_library = _library_call_from(
    os.path.join(os.path.dirname(contextlib.__file__), "site-packages", "lib.py")
)
# A sibling distribution whose directory name starts with "pydeflate".
_pydeflate_named_library = _library_call_from(
    os.path.dirname(pydeflate.context.__file__) + "_extras" + os.sep + "lib.py"
)


class TestPydeflateContext:
    """Test PydeflateContext creation and configuration."""

    def test_create_with_defaults(self, tmp_path):
        """Context can be created with default settings."""
        ctx = PydeflateContext.create(data_dir=tmp_path)

        assert ctx.data_dir == tmp_path
        assert ctx.log_level is None
        assert ctx.enable_validation is True
        assert ctx.cache_manager is not None
        assert ctx.logger is logging.getLogger("pydeflate")

    @pytest.mark.parametrize(
        "make_context",
        [
            pytest.param(_construct_with_log_level, id="dataclass"),
            pytest.param(_create_with_log_level, id="create"),
            pytest.param(_session_with_log_level, id="pydeflate_session"),
            pytest.param(_temporary_with_log_level, id="temporary_context"),
            pytest.param(_subclass_with_log_level, id="subclass_init"),
            pytest.param(_site_packages_library, id="library_under_stdlib_dir"),
            pytest.param(_pydeflate_named_library, id="library_named_pydeflate_x"),
        ],
    )
    def test_log_level_warns_at_caller_and_changes_nothing(
        self, tmp_path, make_context
    ):
        """Passing log_level warns once, names the caller's file, sets no level."""
        set_default_context(PydeflateContext.create(data_dir=tmp_path))
        pkg_logger = logging.getLogger("pydeflate")
        level_before = pkg_logger.level

        with pytest.warns(DeprecationWarning, match="log_level") as record:
            caller_file = make_context(tmp_path)

        assert len(record) == 1
        assert record[0].filename == caller_file
        assert pkg_logger.level == level_before

    def test_create_with_validation_disabled(self, tmp_path):
        """Context can disable schema validation."""
        ctx = PydeflateContext.create(data_dir=tmp_path, enable_validation=False)

        assert ctx.enable_validation is False

    def test_create_with_custom_config(self, tmp_path):
        """Context can accept additional configuration."""
        ctx = PydeflateContext.create(
            data_dir=tmp_path,
            custom_option="value",
            another_option=42,
        )

        assert ctx.config["custom_option"] == "value"
        assert ctx.config["another_option"] == 42

    def test_data_dir_is_created(self, tmp_path):
        """Context creates data directory if it doesn't exist."""
        new_dir = tmp_path / "new_cache"
        assert not new_dir.exists()

        PydeflateContext.create(data_dir=new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_cache_manager_uses_correct_directory(self, tmp_path):
        """CacheManager should use the context's data_dir."""
        ctx = PydeflateContext.create(data_dir=tmp_path)

        assert ctx.cache_manager.base_dir == tmp_path


class TestDefaultContext:
    """Test default context management."""

    def test_get_default_context_creates_if_needed(self):
        """get_default_context creates a context if none exists."""
        ctx = get_default_context()

        assert isinstance(ctx, PydeflateContext)
        assert ctx.data_dir.exists()

    def test_set_default_context_changes_default(self, tmp_path):
        """set_default_context changes the default for the thread."""
        custom_ctx = PydeflateContext.create(data_dir=tmp_path)
        set_default_context(custom_ctx)

        assert get_default_context() is custom_ctx

    def test_default_context_is_thread_local(self, tmp_path):
        """Default context should be thread-local."""
        import threading

        ctx1 = PydeflateContext.create(data_dir=tmp_path / "ctx1")
        ctx2_holder = []

        def thread_func():
            # This thread should get a different default context
            ctx2 = PydeflateContext.create(data_dir=tmp_path / "ctx2")
            set_default_context(ctx2)
            ctx2_holder.append(get_default_context())

        # Set context in main thread
        set_default_context(ctx1)

        # Create and run thread
        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        # Main thread should still have ctx1
        assert get_default_context() is ctx1

        # Other thread should have had ctx2
        assert len(ctx2_holder) == 1
        assert ctx2_holder[0].data_dir == tmp_path / "ctx2"


class TestPydeflateSession:
    """Test pydeflate_session context manager."""

    def test_session_creates_temporary_context(self, tmp_path):
        """pydeflate_session creates a temporary context."""
        with pydeflate_session(data_dir=tmp_path) as ctx:
            assert isinstance(ctx, PydeflateContext)
            assert ctx.data_dir == tmp_path

    def test_session_sets_as_default(self, tmp_path):
        """Context from session becomes default within the block."""
        with pydeflate_session(data_dir=tmp_path) as ctx:
            assert get_default_context() is ctx

    def test_session_restores_previous_context(self, tmp_path):
        """Session restores previous default context when exiting."""
        original = PydeflateContext.create(data_dir=tmp_path / "original")
        set_default_context(original)

        with pydeflate_session(data_dir=tmp_path / "session"):
            # Inside session, default should be different
            assert get_default_context().data_dir == tmp_path / "session"

        # After session, should restore original
        assert get_default_context() is original

    def test_session_restores_on_exception(self, tmp_path):
        """Session restores context even if exception is raised."""
        original = PydeflateContext.create(data_dir=tmp_path / "original")
        set_default_context(original)

        try:
            with pydeflate_session(data_dir=tmp_path / "session"):
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still restore original
        assert get_default_context() is original

    def test_session_accepts_custom_config(self, tmp_path):
        """Session can accept custom configuration options."""
        with pydeflate_session(
            data_dir=tmp_path,
            enable_validation=False,
            custom_key="custom_value",
        ) as ctx:
            assert ctx.enable_validation is False
            assert ctx.config["custom_key"] == "custom_value"


class TestTemporaryContext:
    """Test temporary_context helper."""

    def test_temporary_context_inherits_defaults(self, tmp_path):
        """temporary_context inherits from current default."""
        original = PydeflateContext.create(
            data_dir=tmp_path,
            enable_validation=False,
            custom_setting="value",
        )
        set_default_context(original)

        with temporary_context() as ctx:
            assert ctx.data_dir == tmp_path
            assert ctx.enable_validation is False
            assert ctx.config["custom_setting"] == "value"

    def test_temporary_context_does_not_repeat_log_level_warning(self, tmp_path):
        """A default built with log_level does not make temporary_context warn."""
        with pytest.warns(DeprecationWarning):
            original = PydeflateContext.create(
                data_dir=tmp_path, log_level=logging.WARNING
            )
        set_default_context(original)

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with temporary_context() as ctx:
                assert ctx.log_level is None

    def test_temporary_context_with_overrides(self, tmp_path):
        """temporary_context can override specific settings."""
        original = PydeflateContext.create(
            data_dir=tmp_path / "original",
        )
        set_default_context(original)

        with temporary_context(enable_validation=False) as ctx:
            # Validation should be overridden
            assert ctx.enable_validation is False
            # Data dir should be inherited
            assert ctx.data_dir == tmp_path / "original"

    def test_temporary_context_restores_default(self, tmp_path):
        """temporary_context restores original default."""
        original = PydeflateContext.create(data_dir=tmp_path)
        set_default_context(original)

        with temporary_context(enable_validation=False):
            # Inside, different context
            assert get_default_context().enable_validation is False

        # After, back to original
        assert get_default_context() is original
        assert get_default_context().enable_validation is True


class TestProtocolAcceptance:
    """Test that PydeflateContext accepts any CacheManagerProtocol implementation."""

    def test_context_accepts_protocol_implementations(self, tmp_path):
        """Context field is widened to CacheManagerProtocol — any conforming
        stub can be injected without inheriting from BulkCacheManager."""

        class StubCacheManager:
            def __init__(self) -> None:
                self.base_dir: Path = tmp_path

            def ensure(self, entry, *, refresh: bool = False) -> Path:
                return self.base_dir / "stub.parquet"

            def clear(self, key: str | None = None) -> None:
                pass

        stub = StubCacheManager()
        ctx = PydeflateContext(data_dir=tmp_path, cache_manager=stub)
        assert ctx.cache_manager is stub


class TestContextIsolation:
    """Test that contexts are properly isolated."""

    def test_different_contexts_have_different_caches(self, tmp_path):
        """Different contexts should have independent cache managers."""
        ctx1 = PydeflateContext.create(data_dir=tmp_path / "cache1")
        ctx2 = PydeflateContext.create(data_dir=tmp_path / "cache2")

        assert ctx1.cache_manager is not ctx2.cache_manager
        assert ctx1.cache_manager.base_dir != ctx2.cache_manager.base_dir

    def test_contexts_share_package_logger_and_configure_nothing(self, tmp_path):
        """Contexts use the package logger and leave its configuration alone."""
        pkg_logger = logging.getLogger("pydeflate")
        before = (pkg_logger.level, list(pkg_logger.handlers), pkg_logger.propagate)
        loggers_before = set(logging.Logger.manager.loggerDict)

        ctx1 = PydeflateContext.create(data_dir=tmp_path)
        ctx2 = PydeflateContext.create(data_dir=tmp_path)

        assert ctx1.logger is pkg_logger
        assert ctx2.logger is pkg_logger
        assert (pkg_logger.level, pkg_logger.handlers, pkg_logger.propagate) == before
        assert set(logging.Logger.manager.loggerDict) == loggers_before

    def test_contexts_do_not_share_config(self, tmp_path):
        """Different contexts should have independent config dicts."""
        ctx1 = PydeflateContext.create(data_dir=tmp_path, setting1="value1")
        ctx2 = PydeflateContext.create(data_dir=tmp_path, setting2="value2")

        assert "setting1" in ctx1.config
        assert "setting1" not in ctx2.config
        assert "setting2" in ctx2.config
        assert "setting2" not in ctx1.config

        # Modifying one should not affect the other
        ctx1.config["new_setting"] = "new_value"
        assert "new_setting" not in ctx2.config
