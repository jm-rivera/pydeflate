"""Plugin system for custom data sources.

This module provides a registry-based plugin architecture that allows
users to register custom data sources without modifying pydeflate's code.

Example:
    >>> from pydeflate.plugins import register_source
    >>> from pydeflate.protocols import SourceProtocol
    >>>
    >>> @register_source("my_custom_source")
    >>> class MyCustomSource:
    ...     def __init__(self, update: bool = False):
    ...         self.name = "my_custom_source"
    ...         self.data = load_my_data(update)
    ...         self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]
    ...
    ...     def lcu_usd_exchange(self): ...
    ...     def price_deflator(self, kind): ...
    ...     def validate(self): ...
    >>>
    >>> # Now use it:
    >>> result = deflate_with_source("my_custom_source", data=df, ...)
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from pydeflate.exceptions import PluginError
from pydeflate.protocols import SourceProtocol

# Type variable for source classes
SourceType = TypeVar("SourceType", bound=type)


class SourceRegistry:
    """Registry for data source implementations.

    This class maintains a mapping of source names to their implementation
    classes. It provides methods to register, retrieve, and list sources.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._sources: dict[str, type] = {}
        self._factories: dict[str, Callable[..., SourceProtocol]] = {}

    def register(
        self,
        name: str,
        source_class: type | None = None,
        factory: Callable[..., SourceProtocol] | None = None,
        *,
        override: bool = False,
    ) -> None:
        """Register a data source.

        Args:
            name: Unique name for this source (e.g., 'IMF', 'WorldBank')
            source_class: Class that implements SourceProtocol
            factory: Factory function that returns a SourceProtocol instance
            override: If True, allow replacing existing sources

        Raises:
            PluginError: If name already registered and override=False
            PluginError: If neither source_class nor factory is provided
            PluginError: If source doesn't implement SourceProtocol
        """
        # Validation
        if source_class is None and factory is None:
            raise PluginError(
                "Must provide either source_class or factory",
                plugin_name=name,
            )

        if not override and name in self._sources:
            raise PluginError(
                f"Source '{name}' already registered. Use override=True to replace.",
                plugin_name=name,
            )

        # Check protocol conformance if source_class provided
        if source_class is not None:
            if not self._check_protocol_conformance(source_class):
                raise PluginError(
                    f"Source class must implement SourceProtocol",
                    plugin_name=name,
                )
            self._sources[name] = source_class

        if factory is not None:
            self._factories[name] = factory

    def _check_protocol_conformance(self, source_class: type) -> bool:
        """Check if a class implements SourceProtocol.

        Args:
            source_class: Class to check

        Returns:
            True if class implements the protocol
        """
        required_methods = ["lcu_usd_exchange", "price_deflator", "validate"]
        required_attrs = ["name", "data", "_idx"]

        for method in required_methods:
            if not hasattr(source_class, method):
                return False
            if not callable(getattr(source_class, method)):
                return False

        # Check that class can be instantiated and has required attributes
        # Note: We can't fully check this without instantiation,
        # so we just check the class has these as class attributes or in __init__
        # This is a best-effort check
        return True

    def get(self, name: str, **kwargs) -> SourceProtocol:
        """Get a source instance by name.

        Args:
            name: Name of the registered source
            **kwargs: Keyword arguments to pass to source constructor

        Returns:
            Instance of the source

        Raises:
            PluginError: If source not found
        """
        # Try factory first
        if name in self._factories:
            try:
                return self._factories[name](**kwargs)
            except Exception as e:
                raise PluginError(
                    f"Factory function failed: {e}",
                    plugin_name=name,
                ) from e

        # Try class
        if name in self._sources:
            try:
                return self._sources[name](**kwargs)
            except Exception as e:
                raise PluginError(
                    f"Source instantiation failed: {e}",
                    plugin_name=name,
                ) from e

        raise PluginError(
            f"Source '{name}' not found. Available sources: {self.list_sources()}",
            plugin_name=name,
        )

    def list_sources(self) -> list[str]:
        """List all registered source names.

        Returns:
            List of source names
        """
        all_names = set(self._sources.keys()) | set(self._factories.keys())
        return sorted(all_names)

    def is_registered(self, name: str) -> bool:
        """Check if a source is registered.

        Args:
            name: Source name to check

        Returns:
            True if registered
        """
        return name in self._sources or name in self._factories

    def unregister(self, name: str) -> None:
        """Remove a source from the registry.

        Args:
            name: Source name to remove

        Raises:
            PluginError: If source not found
        """
        if not self.is_registered(name):
            raise PluginError(
                f"Cannot unregister '{name}': not found",
                plugin_name=name,
            )

        self._sources.pop(name, None)
        self._factories.pop(name, None)


# Global registry instance
_global_registry = SourceRegistry()


def register_source(
    name: str,
    *,
    override: bool = False,
) -> Callable[[SourceType], SourceType]:
    """Decorator to register a source class.

    Example:
        >>> @register_source("my_source")
        ... class MySource:
        ...     def __init__(self, update: bool = False):
        ...         self.name = "my_source"
        ...         ...
        ...
        ...     def lcu_usd_exchange(self): ...
        ...     def price_deflator(self, kind): ...

    Args:
        name: Unique name for this source
        override: Allow replacing existing sources

    Returns:
        Decorator function
    """

    def decorator(cls: SourceType) -> SourceType:
        _global_registry.register(name, source_class=cls, override=override)
        return cls

    return decorator


def get_source(name: str, **kwargs) -> SourceProtocol:
    """Get a registered source instance.

    Args:
        name: Name of the source
        **kwargs: Arguments to pass to source constructor

    Returns:
        Source instance

    Raises:
        PluginError: If source not found or instantiation fails
    """
    return _global_registry.get(name, **kwargs)


def list_sources() -> list[str]:
    """List all available sources.

    Returns:
        Sorted list of source names
    """
    return _global_registry.list_sources()


def is_source_registered(name: str) -> bool:
    """Check if a source is registered.

    Args:
        name: Source name

    Returns:
        True if registered
    """
    return _global_registry.is_registered(name)


# Pre-register built-in sources
def _register_builtin_sources():
    """Register pydeflate's built-in sources."""
    from pydeflate.core.source import DAC, IMF, WorldBank, WorldBankPPP

    _global_registry.register("IMF", source_class=IMF, override=True)
    _global_registry.register("World Bank", source_class=WorldBank, override=True)
    _global_registry.register(
        "World Bank PPP", source_class=WorldBankPPP, override=True
    )
    _global_registry.register("DAC", source_class=DAC, override=True)

    # Aliases for convenience
    _global_registry.register("imf", source_class=IMF, override=True)
    _global_registry.register("wb", source_class=WorldBank, override=True)
    _global_registry.register("worldbank", source_class=WorldBank, override=True)
    _global_registry.register("dac", source_class=DAC, override=True)
    _global_registry.register("oecd", source_class=DAC, override=True)


# Register built-in sources when module is imported
_register_builtin_sources()
