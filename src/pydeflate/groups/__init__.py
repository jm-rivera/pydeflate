"""Country group registry and configuration.

Manages how pydeflate treats aggregate rows for country groups
(e.g., Euro Area, DAC members) in source data.

Usage:
    from pydeflate.groups import _registry

    # Check if a currency maps to a known group
    _registry.find_by_iso3("EUR")  # GroupDefinition(key="EMU", ...)

    # Get group definition by key
    group = _registry.get("EMU")
    group.get_members(2023)  # ['AUT', 'BEL', ..., 'HRV']

    # Configure treatment
    _registry.configure("EMU", treatment="fixed", members_year=2019)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class GroupTreatment(str, Enum):
    """How pydeflate computes deflators for country group rows.

    SOURCE: Use the data source's own published aggregate (default).
        Fast, backward-compatible. Methodology varies by source.

    FIXED: GDP-weighted average using the latest/current membership for all years.
        Comparable across time. Historically inaccurate for pre-accession years.

    DYNAMIC: GDP-weighted average using the actual membership in each year.
        Historically accurate. Creates composition-change artifacts at accession years.
    """

    SOURCE = "source"
    FIXED = "fixed"
    DYNAMIC = "dynamic"


@dataclass(frozen=True)
class GroupDefinition:
    """A country group recognized in source data.

    Attributes:
        key: User-facing identifier for this group (e.g., "EMU").
        iso3: ISO3 code used for this group in source data (e.g., "EUR").
        name: Human-readable name (e.g., "Euro Area (EMU)").
        get_members: Function returning member ISO3 codes for a given year.
    """

    key: str
    iso3: str
    name: str
    get_members: Callable[[int], list[str]]


@dataclass
class GroupConfig:
    """Runtime configuration for a specific group."""

    treatment: GroupTreatment = GroupTreatment.SOURCE
    members_year: int | None = None


class GroupRegistry:
    """Registry of known country groups and their treatment configs.

    Groups are registered by ``key`` (e.g., "EMU") and looked up either by
    key (public API) or by ``iso3`` (internal currency-to-group resolution).

    Note: This registry uses module-level state and is not thread-safe.
    For thread-isolated configuration, use ``pydeflate_session``.
    """

    def __init__(self) -> None:
        self._groups: dict[str, GroupDefinition] = {}
        self._iso3_to_key: dict[str, str] = {}
        self._configs: dict[str, GroupConfig] = {}
        self._default_treatment: GroupTreatment = GroupTreatment.SOURCE

    def register(self, group: GroupDefinition) -> None:
        """Register a country group."""
        self._groups[group.key] = group
        self._iso3_to_key[group.iso3] = group.key

    def get(self, key: str) -> GroupDefinition | None:
        """Get group definition by key (e.g., "EMU")."""
        return self._groups.get(key)

    def find_by_iso3(self, iso3: str) -> GroupDefinition | None:
        """Find group by its source-data ISO3 code (e.g., "EUR")."""
        key = self._iso3_to_key.get(iso3)
        if key is None:
            return None
        return self._groups.get(key)

    def configure(
        self,
        key: str,
        *,
        treatment: str | GroupTreatment,
        members_year: int | None = None,
    ) -> None:
        """Set per-group configuration."""
        if key not in self._groups:
            raise ValueError(
                f"Unknown group '{key}'. Registered groups: {self.list_groups()}"
            )
        self._configs[key] = GroupConfig(
            treatment=GroupTreatment(treatment),
            members_year=members_year,
        )

    def get_config(self, key: str) -> GroupConfig:
        """Get effective config (per-group override or global default)."""
        if key in self._configs:
            return self._configs[key]
        return GroupConfig(treatment=self._default_treatment)

    @property
    def default_treatment(self) -> GroupTreatment:
        """Get the default treatment for all groups."""
        return self._default_treatment

    @default_treatment.setter
    def default_treatment(self, value: GroupTreatment | str) -> None:
        """Set the default treatment for all groups."""
        self._default_treatment = GroupTreatment(value)

    def list_groups(self) -> list[str]:
        """List all registered group keys."""
        return sorted(self._groups.keys())

    def snapshot(self) -> tuple[GroupTreatment, dict[str, GroupConfig]]:
        """Capture current state for later restoration."""
        return self._default_treatment, self._configs.copy()

    def restore(self, state: tuple[GroupTreatment, dict[str, GroupConfig]]) -> None:
        """Restore previously captured state."""
        self._default_treatment, self._configs = state

    def reset(self) -> None:
        """Reset all configs to defaults (keeps registrations)."""
        self._configs.clear()
        self._default_treatment = GroupTreatment.SOURCE


# Module-level singleton
_registry = GroupRegistry()


def _register_builtin_groups() -> None:
    """Register pydeflate's built-in groups."""
    from pydeflate.groups.emu import members_for_year

    _registry.register(
        GroupDefinition(
            key="EMU",
            iso3="EUR",
            name="Euro Area (EMU)",
            get_members=members_for_year,
        )
    )


_register_builtin_groups()
