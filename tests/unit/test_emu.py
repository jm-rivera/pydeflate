from pydeflate.groups.emu import (
    accession_year,
    all_members,
    is_member,
    members_for_year,
)


class TestEMUMembership:
    def test_founding_members_1999(self):
        members = members_for_year(1999)
        assert "DEU" in members
        assert "FRA" in members
        assert "ITA" in members
        assert "ESP" in members
        assert len(members) == 11

    def test_greece_joins_2001(self):
        assert "GRC" not in members_for_year(2000)
        assert "GRC" in members_for_year(2001)

    def test_croatia_joins_2023(self):
        assert "HRV" not in members_for_year(2022)
        assert "HRV" in members_for_year(2023)

    def test_all_members_returns_20(self):
        assert len(all_members()) == 20
        assert "HRV" in all_members()

    def test_accession_year(self):
        assert accession_year("DEU") == 1999
        assert accession_year("GRC") == 2001
        assert accession_year("HRV") == 2023
        assert accession_year("USA") is None

    def test_is_member(self):
        assert is_member("DEU", 2020) is True
        assert is_member("HRV", 2022) is False
        assert is_member("HRV", 2023) is True
        assert is_member("USA", 2020) is False

    def test_pre_euro_returns_empty(self):
        assert members_for_year(1998) == []

    def test_2023_includes_all_20(self):
        assert len(members_for_year(2023)) == 20
