"""Custom exception hierarchy for pydeflate.

This module defines specific exception types that allow users to handle
different failure modes appropriately (e.g., retry on network errors,
fail fast on validation errors).
"""

from __future__ import annotations


class PydeflateError(Exception):
    """Base exception for all pydeflate errors.

    All exceptions raised by pydeflate inherit from this class,
    making it easy to catch all pydeflate-specific errors.
    """

    pass


class DataSourceError(PydeflateError):
    """Raised when there's an issue with a data source.

    This is a base class for all data source related errors.
    """

    def __init__(self, message: str, source: str | None = None):
        """Initialize DataSourceError.

        Args:
            message: Description of the error
            source: Name of the data source (e.g., 'IMF', 'World Bank')
        """
        self.source = source
        super().__init__(f"[{source}] {message}" if source else message)


class NetworkError(DataSourceError):
    """Raised when network operations fail.

    This typically indicates a transient error that might succeed on retry.
    """

    pass


class SchemaValidationError(DataSourceError):
    """Raised when data doesn't match expected schema.

    This indicates a problem with the data structure, either from:
    - External API changes
    - Corrupted downloaded data
    - User input with wrong columns/types
    """

    def __init__(
        self,
        message: str,
        source: str | None = None,
        expected_schema: dict | None = None,
        actual_schema: dict | None = None,
    ):
        """Initialize SchemaValidationError.

        Args:
            message: Description of validation failure
            source: Name of the data source
            expected_schema: Expected column types/names
            actual_schema: Actual column types/names found
        """
        self.expected_schema = expected_schema
        self.actual_schema = actual_schema
        super().__init__(message, source)


class CacheError(PydeflateError):
    """Raised when cache operations fail.

    Examples:
    - Unable to write to cache directory
    - Corrupted cache files
    - Lock file acquisition timeout
    """

    def __init__(self, message: str, cache_path: str | None = None):
        """Initialize CacheError.

        Args:
            message: Description of cache error
            cache_path: Path to the cache file/directory involved
        """
        self.cache_path = cache_path
        super().__init__(
            f"Cache error at {cache_path}: {message}" if cache_path else message
        )


class ConfigurationError(PydeflateError):
    """Raised when configuration parameters are invalid.

    Examples:
    - Invalid currency code
    - Base year out of range
    - Missing required columns in user data
    - Conflicting parameter combinations
    """

    def __init__(self, message: str, parameter: str | None = None):
        """Initialize ConfigurationError.

        Args:
            message: Description of configuration issue
            parameter: Name of the problematic parameter
        """
        self.parameter = parameter
        super().__init__(
            f"Invalid configuration for '{parameter}': {message}"
            if parameter
            else message
        )


class MissingDataError(PydeflateError):
    """Raised when required deflator or exchange data is unavailable.

    This occurs when:
    - Requested country/year combination has no data in the source
    - Data gaps in historical records
    - Future years beyond available estimates
    """

    def __init__(
        self,
        message: str,
        missing_entities: dict[str, list[int]] | None = None,
    ):
        """Initialize MissingDataError.

        Args:
            message: Description of missing data
            missing_entities: Dict mapping entity codes to missing years
        """
        self.missing_entities = missing_entities
        super().__init__(message)


class PluginError(PydeflateError):
    """Raised when plugin registration or loading fails.

    Examples:
    - Plugin doesn't implement required protocol
    - Plugin name conflicts with existing source
    - Plugin initialization fails
    """

    def __init__(self, message: str, plugin_name: str | None = None):
        """Initialize PluginError.

        Args:
            message: Description of plugin error
            plugin_name: Name of the plugin that failed
        """
        self.plugin_name = plugin_name
        super().__init__(
            f"Plugin '{plugin_name}' error: {message}" if plugin_name else message
        )
