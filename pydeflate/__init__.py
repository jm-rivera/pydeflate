__author__ = """Jorge Rivera"""
__email__ = "jorge.rivera@one.org"
__version__ = '1.0.1'


from pydeflate.deflate.deflate import deflate
from pydeflate.tools.exchange import exchange
from pydeflate.tools.update_data import update_all_data
from pydeflate.utils import warn_updates

#check that data is fresh enough
warn_updates()


