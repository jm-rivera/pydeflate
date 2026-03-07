"""Tests for group registry, types, and configuration."""

import pytest

from pydeflate.groups import (
    GroupDefinition,
    GroupTreatment,
    _registry,
)


class TestGroupTreatment:
    def test_values(self):
        assert GroupTreatment.SOURCE == "source"
        assert GroupTreatment.FIXED == "fixed"
        assert GroupTreatment.DYNAMIC == "dynamic"

    def test_from_string(self):
        assert GroupTreatment("source") == GroupTreatment.SOURCE
        assert GroupTreatment("fixed") == GroupTreatment.FIXED
        assert GroupTreatment("dynamic") == GroupTreatment.DYNAMIC


class TestGroupRegistry:
    def test_eur_registered_by_default(self):
        assert _registry.is_group("EUR")

    def test_eur_definition(self):
        group = _registry.get("EUR")
        assert group is not None
        assert group.name == "Euro Area (EMU)"
        assert group.iso3 == "EUR"

    def test_eur_members_callable(self):
        group = _registry.get("EUR")
        members = group.get_members(2023)
        assert "HRV" in members
        assert len(members) == 20

    def test_unknown_group(self):
        assert not _registry.is_group("XYZ")
        assert _registry.get("XYZ") is None

    def test_default_treatment_is_source(self):
        assert _registry.default_treatment == GroupTreatment.SOURCE

    def test_set_default_treatment(self):
        original = _registry.default_treatment
        try:
            _registry.default_treatment = "fixed"
            assert _registry.default_treatment == GroupTreatment.FIXED
        finally:
            _registry.default_treatment = original

    def test_configure_group(self):
        try:
            _registry.configure("EUR", treatment="fixed", members_year=2019)
            config = _registry.get_config("EUR")
            assert config.treatment == GroupTreatment.FIXED
            assert config.members_year == 2019
        finally:
            _registry.reset()

    def test_configure_unknown_group_raises(self):
        with pytest.raises(ValueError, match="Unknown group"):
            _registry.configure("XYZ", treatment="fixed")

    def test_get_config_falls_back_to_default(self):
        config = _registry.get_config("EUR")
        assert config.treatment == _registry.default_treatment

    def test_reset_clears_configs(self):
        _registry.configure("EUR", treatment="dynamic")
        _registry.default_treatment = "fixed"
        _registry.reset()
        assert _registry.default_treatment == GroupTreatment.SOURCE
        config = _registry.get_config("EUR")
        assert config.treatment == GroupTreatment.SOURCE

    def test_list_groups(self):
        groups = _registry.list_groups()
        assert "EUR" in groups

    def test_register_custom_group(self):
        try:
            _registry.register(
                GroupDefinition(
                    iso3="TEST",
                    name="Test Group",
                    get_members=lambda year: ["AAA", "BBB"],
                )
            )
            assert _registry.is_group("TEST")
            group = _registry.get("TEST")
            assert group.get_members(2023) == ["AAA", "BBB"]
        finally:
            _registry._groups.pop("TEST", None)

    def test_snapshot_and_restore(self):
        state = _registry.snapshot()
        _registry.configure("EUR", treatment="dynamic", members_year=2019)
        _registry.default_treatment = "fixed"
        assert _registry.default_treatment == GroupTreatment.FIXED
        _registry.restore(state)
        assert _registry.default_treatment == GroupTreatment.SOURCE
        config = _registry.get_config("EUR")
        assert config.members_year is None
