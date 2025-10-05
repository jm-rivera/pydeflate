"""Tests for custom exception hierarchy."""

import pytest

from pydeflate.exceptions import (
    CacheError,
    ConfigurationError,
    DataSourceError,
    MissingDataError,
    NetworkError,
    PluginError,
    PydeflateError,
    SchemaValidationError,
)


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """All pydeflate exceptions should inherit from PydeflateError."""
        exceptions = [
            DataSourceError,
            NetworkError,
            SchemaValidationError,
            CacheError,
            ConfigurationError,
            MissingDataError,
            PluginError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, PydeflateError)
            assert issubclass(exc_class, Exception)

    def test_data_source_error_subclasses(self):
        """NetworkError and SchemaValidationError should inherit from DataSourceError."""
        assert issubclass(NetworkError, DataSourceError)
        assert issubclass(SchemaValidationError, DataSourceError)

    def test_base_exception_is_catchable(self):
        """Should be able to catch all pydeflate errors with base class."""
        with pytest.raises(PydeflateError):
            raise ConfigurationError("test")

        with pytest.raises(PydeflateError):
            raise DataSourceError("test")

        with pytest.raises(PydeflateError):
            raise CacheError("test")


class TestDataSourceError:
    """Test DataSourceError and subclasses."""

    def test_data_source_error_with_source_name(self):
        """DataSourceError should include source name in message."""
        exc = DataSourceError("Connection failed", source="IMF")

        assert "IMF" in str(exc)
        assert "Connection failed" in str(exc)
        assert exc.source == "IMF"

    def test_data_source_error_without_source_name(self):
        """DataSourceError should work without source name."""
        exc = DataSourceError("Generic error")

        assert "Generic error" in str(exc)
        assert exc.source is None

    def test_network_error_is_data_source_error(self):
        """NetworkError should behave like DataSourceError."""
        exc = NetworkError("Timeout", source="World Bank")

        assert isinstance(exc, DataSourceError)
        assert "World Bank" in str(exc)
        assert exc.source == "World Bank"

    def test_schema_validation_error_with_schemas(self):
        """SchemaValidationError can include expected and actual schemas."""
        expected = {"col1": "int", "col2": "float"}
        actual = {"col1": "str", "col2": "float"}

        exc = SchemaValidationError(
            "Type mismatch",
            source="IMF",
            expected_schema=expected,
            actual_schema=actual,
        )

        assert exc.expected_schema == expected
        assert exc.actual_schema == actual
        assert "IMF" in str(exc)


class TestCacheError:
    """Test CacheError."""

    def test_cache_error_with_path(self):
        """CacheError should include cache path in message."""
        exc = CacheError("Write failed", cache_path="/tmp/cache/file.parquet")

        assert "/tmp/cache/file.parquet" in str(exc)
        assert "Write failed" in str(exc)
        assert exc.cache_path == "/tmp/cache/file.parquet"

    def test_cache_error_without_path(self):
        """CacheError should work without path."""
        exc = CacheError("Generic cache error")

        assert "Generic cache error" in str(exc)
        assert exc.cache_path is None


class TestConfigurationError:
    """Test ConfigurationError."""

    def test_configuration_error_with_parameter(self):
        """ConfigurationError should include parameter name."""
        exc = ConfigurationError("Invalid currency", parameter="source_currency")

        assert "source_currency" in str(exc)
        assert "Invalid currency" in str(exc)
        assert exc.parameter == "source_currency"

    def test_configuration_error_without_parameter(self):
        """ConfigurationError should work without parameter name."""
        exc = ConfigurationError("General configuration issue")

        assert "General configuration issue" in str(exc)
        assert exc.parameter is None


class TestMissingDataError:
    """Test MissingDataError."""

    def test_missing_data_error_with_entities(self):
        """MissingDataError can track missing entities and years."""
        missing = {
            "USA": [2015, 2016, 2017],
            "FRA": [2020],
        }

        exc = MissingDataError("Data unavailable", missing_entities=missing)

        assert exc.missing_entities == missing
        assert "Data unavailable" in str(exc)

    def test_missing_data_error_without_entities(self):
        """MissingDataError should work without entity details."""
        exc = MissingDataError("Some data missing")

        assert "Some data missing" in str(exc)
        assert exc.missing_entities is None


class TestPluginError:
    """Test PluginError."""

    def test_plugin_error_with_plugin_name(self):
        """PluginError should include plugin name in message."""
        exc = PluginError("Registration failed", plugin_name="custom_source")

        assert "custom_source" in str(exc)
        assert "Registration failed" in str(exc)
        assert exc.plugin_name == "custom_source"

    def test_plugin_error_without_plugin_name(self):
        """PluginError should work without plugin name."""
        exc = PluginError("General plugin error")

        assert "General plugin error" in str(exc)
        assert exc.plugin_name is None


class TestExceptionChaining:
    """Test exception chaining with 'from' clause."""

    def test_exception_chaining_preserves_cause(self):
        """Exceptions should preserve original cause when chained."""
        original = ValueError("Original error")

        try:
            try:
                raise original
            except ValueError as e:
                raise DataSourceError("Wrapped error", source="IMF") from e
        except DataSourceError as exc:
            assert exc.__cause__ is original
            assert str(exc.__cause__) == "Original error"
