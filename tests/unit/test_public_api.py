"""Test public API exports for group support."""

import pytest

from pydeflate import (
    GroupTreatment,
    configure_group,
    emu_members,
    reset_group_config,
    set_group_treatment,
)
from pydeflate.groups import _registry


class TestPublicGroupAPI:
    def test_set_group_treatment(self):
        set_group_treatment("fixed")
        assert _registry.default_treatment == GroupTreatment.FIXED

    def test_configure_group(self):
        configure_group("EUR", treatment="fixed", members_year=2019)
        config = _registry.get_config("EUR")
        assert config.treatment == GroupTreatment.FIXED
        assert config.members_year == 2019

    def test_reset_group_config(self):
        set_group_treatment("dynamic")
        configure_group("EUR", treatment="fixed")
        reset_group_config()
        assert _registry.default_treatment == GroupTreatment.SOURCE

    def test_configure_unknown_group_raises(self):
        with pytest.raises(ValueError):
            configure_group("XYZ", treatment="fixed")

    def test_group_treatment_exported(self):
        assert GroupTreatment.FIXED == "fixed"


class TestEmuMembersPublic:
    def test_default_returns_all(self):
        members = emu_members()
        assert len(members) == 20
        assert "DEU" in members

    def test_with_year(self):
        members = emu_members(1999)
        assert len(members) == 11
        assert "GRC" not in members

    def test_2023_includes_croatia(self):
        members = emu_members(2023)
        assert "HRV" in members
