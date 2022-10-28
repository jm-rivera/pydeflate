import os

from pydeflate.config import PYDEFLATE_PATHS
from pydeflate.get_data.oecd_data import OECD_XE, OECD


def test_update():
    test_obj = OECD_XE()
    test_obj2 = OECD()

    last_update_dac1 = os.path.getmtime(PYDEFLATE_PATHS.data + r"/dac1.feather")

    test_obj.update()

    assert os.path.getmtime(PYDEFLATE_PATHS.data + r"/dac1.feather") > last_update_dac1

    last_update_dac1_2 = os.path.getmtime(PYDEFLATE_PATHS.data + r"/dac1.feather")
    test_obj2.update()

    assert os.path.getmtime(PYDEFLATE_PATHS.data + r"/dac1.feather") > last_update_dac1_2


def test_load_data():
    test_obj_xe = OECD_XE()
    test_obj_xe.load_data()

    test_obj = OECD()
    test_obj.load_data()

    xe_obj = test_obj_xe.data
    defl_obj = test_obj.data

    assert len(xe_obj) > 1
    assert len(defl_obj) > 1
    assert xe_obj.shape[0] > xe_obj.shape[1]
    assert defl_obj.shape[0] > defl_obj.shape[1]


def test_available_methods():
    test_obj_xe = OECD_XE()
    test_obj = OECD()

    assert len(test_obj_xe.available_methods()) > 0
    assert len(test_obj.available_methods()) > 0
    assert all(
        [
            [isinstance(k, str), isinstance(v, str)]
            for k, v in test_obj.available_methods().items()
        ]
    )


def test_get_data():
    test_obj_xe = OECD_XE()
    test_obj = OECD()

    # test not loaded
    df = test_obj_xe.get_data("USA")
    assert len(df) > 0
    assert "USA" in df.iso_code.unique()

    # test loaded
    test_obj_xe2 = OECD_XE()
    test_obj_xe2.load_data()
    df2 = test_obj_xe2.get_data("FRA")
    assert len(df2) > 0
    assert "FRA" in df.iso_code.unique()

    # test not loaded
    df3 = test_obj.get_data()
    assert len(df3) > 0

    # test loaded
    test_obj2 = OECD()
    test_obj2.load_data()
    df4 = test_obj2.get_data()
    assert len(df4) > 0

