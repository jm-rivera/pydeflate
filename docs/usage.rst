=====
Usage
=====

Basic usage
~~~~~~~~~~~

Convert data expressed in current USD prices to constant EUR prices for
a given base year:

.. code:: python

   import pydeflate
   import pandas as pd

   # example data
   data = {'iso_code': ['FRA','USA', 'GTM'],
           'year': [2017, 2017, 2017],
           'value': [50, 100, 200]}

   # create an example dataframe, in current USD prices
   df = pd.DataFrame.from_dict(data)

   # convert to EUR 2015 constant prices
   df_constant = pydeflate.deflate(
       df = df,
       base_year = 2015,
       source = 'wb',
       method = 'gdp',
       source_currency = "USA", # since data is in USD
       target_currency = "EMU", # we want the result in constant EUR
       id_column = "iso_code",
       id_type = "ISO3", # specifying this is optional in most cases
       date_column = "year",
       source_col = "value",
       target_col = "value_constant",
   )

   print(df_constant)

This results in a dataframe containing a new column ``value_constant``
in 2015 constant prices. In the background, pydeflate takes into
account:

-  changes in princes, through a gdp deflator in this case
-  changes in exchange rates overtime

Pydeflate can also handle data that is expressed in local currency
units. In that case, users can specify ``LCU`` as the source currency.

.. code:: python

   import pydeflate
   import pandas as pd

   #example data
   data = {'country': ['United Kingdom','United Kingdom', 'Japan'],
           'date': [2011, 2015, 2015],
           'value': [100, 100, 100]}

   #create an example dataframe, in current local currency units
   df = pd.DataFrame.from_dict(data)

   #convert to USD 2018 constant prices
   df_constant = pydeflate.deflate(
       df = df,
       base_year = 2018,
       source = 'imf',
       method = 'pcpi',
       source_currency = "LCU", #since data is in LCU
       target_currency = "USA", #to get data in USD
       id_column = "iso_code",
       date_column = "date",
       source_col = "value",
       target_col = "value", #to not create a new column
   )

   print(df_constant)

Users can also convert a dataset expressed in constant prices to current
prices using pydeflate. To avoid introducing errors, users should know
which methodology/ data was used to create constant prices by the
original source. The basic usage is the same as before, but the
``to_current`` parameter is set to ``True``.

For example, to convert DAC data expressed in 2016 USD constant prices
to current US dollars:

.. code:: python

   import pydeflate
   import pandas as pd

   #example data
   data = {'dac_code': [302, 4, 4],
           'date': [2010, 2016, 2018],
           'value': [100, 100, 100]}

   #create an example dataframe, in current local currency units
   df = pd.DataFrame.from_dict(data)

   #convert to USD 2018 constant prices
   df_current = pydeflate.deflate(
       df = df,
       base_year = 2016,
       source = 'oecd_dac',
       source_currency = "USA", #since data is in USD constant
       target_currency = "LCU", #to get the current LCU figures
       id_column = "dac_code",
       id_type = "DAC",
       date_column = "date",
       source_col = "value",
       target_col = "value_current",
       to_current = True,
   )

   print(df_current)
