"""Tests for context management and dependency injection."""

import logging
from pathlib import Path

import pytest

from pydeflate.context import (
    PydeflateContext,
    get_default_context,
    pydeflate_session,
    set_default_context,
    temporary_context,
)


class TestPydeflateContext:
    """Test PydeflateContext creation and configuration."""

    def test_create_with_defaults(self, tmp_path):
        """Context can be created with default settings."""
        ctx = PydeflateContext.create(data_dir=tmp_path)

        assert ctx.data_dir == tmp_path
        assert ctx.log_level == logging.INFO
        assert ctx.enable_validation is True
        assert ctx.cache_manager is not None
        assert ctx.logger is not None

    def test_create_with_custom_log_level(self, tmp_path):
        """Context can specify custom log level."""
        ctx = PydeflateContext.create(data_dir=tmp_path, log_level=logging.DEBUG)

        assert ctx.log_level == logging.DEBUG
        assert ctx.logger.level == logging.DEBUG

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

        ctx = PydeflateContext.create(data_dir=new_dir)

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
        custom_ctx = PydeflateContext.create(
            data_dir=tmp_path, log_level=logging.WARNING
        )
        set_default_context(custom_ctx)

        retrieved = get_default_context()

        assert retrieved is custom_ctx
        assert retrieved.log_level == logging.WARNING

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
        with pydeflate_session(data_dir=tmp_path, log_level=logging.DEBUG) as ctx:
            default = get_default_context()
            assert default is ctx
            assert default.log_level == logging.DEBUG

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
            log_level=logging.WARNING,
            custom_setting="value",
        )
        set_default_context(original)

        with temporary_context() as ctx:
            # Should inherit data_dir and log_level
            assert ctx.data_dir == tmp_path
            assert ctx.log_level == logging.WARNING
            assert ctx.config["custom_setting"] == "value"

    def test_temporary_context_with_overrides(self, tmp_path):
        """temporary_context can override specific settings."""
        original = PydeflateContext.create(
            data_dir=tmp_path / "original",
            log_level=logging.INFO,
        )
        set_default_context(original)

        with temporary_context(log_level=logging.DEBUG) as ctx:
            # Log level should be overridden
            assert ctx.log_level == logging.DEBUG
            # Data dir should be inherited
            assert ctx.data_dir == tmp_path / "original"

    def test_temporary_context_restores_default(self, tmp_path):
        """temporary_context restores original default."""
        original = PydeflateContext.create(data_dir=tmp_path)
        set_default_context(original)

        with temporary_context(log_level=logging.DEBUG):
            # Inside, different context
            assert get_default_context().log_level == logging.DEBUG

        # After, back to original
        assert get_default_context() is original
        assert get_default_context().log_level == logging.INFO


class TestContextIsolation:
    """Test that contexts are properly isolated."""

    def test_different_contexts_have_different_caches(self, tmp_path):
        """Different contexts should have independent cache managers."""
        ctx1 = PydeflateContext.create(data_dir=tmp_path / "cache1")
        ctx2 = PydeflateContext.create(data_dir=tmp_path / "cache2")

        assert ctx1.cache_manager is not ctx2.cache_manager
        assert ctx1.cache_manager.base_dir != ctx2.cache_manager.base_dir

    def test_different_contexts_have_different_loggers(self, tmp_path):
        """Different contexts should have independent loggers."""
        ctx1 = PydeflateContext.create(data_dir=tmp_path, log_level=logging.DEBUG)
        ctx2 = PydeflateContext.create(data_dir=tmp_path, log_level=logging.ERROR)

        assert ctx1.logger is not ctx2.logger
        assert ctx1.logger.level == logging.DEBUG
        assert ctx2.logger.level == logging.ERROR

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
