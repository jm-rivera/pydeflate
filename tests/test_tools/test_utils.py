import pytest

from pydeflate.utils import clean_number


def test_clean_number():
    test_number = "1,000,000.00"
    assert clean_number(test_number) == pytest.approx(1_000_000.0)

    test_number = 1_000_000
    assert clean_number(test_number) == pytest.approx(1_000_000.0)

    test_number = ",,"
    assert not clean_number(test_number) == clean_number(test_number)
