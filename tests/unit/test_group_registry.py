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
    def test_emu_registered_by_default(self):
        assert _registry.get("EMU") is not None

    def test_emu_definition(self):
        group = _registry.get("EMU")
        assert group.key == "EMU"
        assert group.iso3 == "EUR"
        assert group.name == "Euro Area (EMU)"

    def test_emu_members_callable(self):
        group = _registry.get("EMU")
        members = group.get_members(2023)
        assert "HRV" in members
        assert len(members) == 20

    def test_find_by_iso3(self):
        group = _registry.find_by_iso3("EUR")
        assert group is not None
        assert group.key == "EMU"

    def test_find_by_iso3_unknown(self):
        assert _registry.find_by_iso3("XYZ") is None

    def test_unknown_group(self):
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
            _registry.configure("EMU", treatment="fixed", members_year=2019)
            config = _registry.get_config("EMU")
            assert config.treatment == GroupTreatment.FIXED
            assert config.members_year == 2019
        finally:
            _registry.reset()

    def test_configure_unknown_group_raises(self):
        with pytest.raises(ValueError, match="Unknown group"):
            _registry.configure("XYZ", treatment="fixed")

    def test_get_config_falls_back_to_default(self):
        config = _registry.get_config("EMU")
        assert config.treatment == _registry.default_treatment

    def test_reset_clears_configs(self):
        _registry.configure("EMU", treatment="dynamic")
        _registry.default_treatment = "fixed"
        _registry.reset()
        assert _registry.default_treatment == GroupTreatment.SOURCE
        config = _registry.get_config("EMU")
        assert config.treatment == GroupTreatment.SOURCE

    def test_list_groups(self):
        groups = _registry.list_groups()
        assert "EMU" in groups

    def test_register_custom_group(self):
        try:
            _registry.register(
                GroupDefinition(
                    key="TEST",
                    iso3="TST",
                    name="Test Group",
                    get_members=lambda year: ["AAA", "BBB"],
                )
            )
            assert _registry.get("TEST") is not None
            assert _registry.find_by_iso3("TST").key == "TEST"
            group = _registry.get("TEST")
            assert group.get_members(2023) == ["AAA", "BBB"]
        finally:
            _registry._groups.pop("TEST", None)
            _registry._iso3_to_key.pop("TST", None)

    def test_snapshot_and_restore(self):
        state = _registry.snapshot()
        _registry.configure("EMU", treatment="dynamic", members_year=2019)
        _registry.default_treatment = "fixed"
        assert _registry.default_treatment == GroupTreatment.FIXED
        _registry.restore(state)
        assert _registry.default_treatment == GroupTreatment.SOURCE
        config = _registry.get_config("EMU")
        assert config.members_year is None
