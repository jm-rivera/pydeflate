=====================
The pydeflate Package
=====================


.. image:: https://img.shields.io/pypi/v/pydeflate.svg
        :target: https://pypi.python.org/pypi/pydeflate

.. image:: https://readthedocs.org/projects/pydeflate/badge/?version=latest
        :target: https://pydeflate.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Pydeflate is a Python package to convert flows data to constant prices. This can be done
from any source currency to any desired base year and currency. Pydeflate can also
be used to convert constant data to current prices and to convert from one currency
to another (in current and constant prices). Users can choose the source of the 
exchange and deflator/prices data (IMF, World Bank or OECD DAC).


* Free software: MIT license
* Documentation: https://pydeflate.readthedocs.io.


Installation
------------

pydeflate is registered at PyPI. From the command line:

::

    pip install pydeflate --upgrade


Alternatively, the source code is available on GitHub_.

.. _GitHub: https://github.com/jm-rivera/pydeflate


Usage
-----

Basic usage
^^^^^^^^^^^

Convert data expressed in current USD prices to constant EUR prices for a given base year:

.. code:: python

    import pydeflate
    import pandas as pd
    
    #example data
    data = {'iso_code': ['FRA','USA', 'GTM'],
            'year': [2017, 2017, 2017],
            'value': [50, 100, 200]}
    
    #create an example dataframe, in current USD prices
    df = pd.DataFrame.from_dict(data)
    
    #convert to EUR 2015 constant prices
    df_constant = pydeflate.deflate(
        df = df,
        base_year = 2015,
        source = 'wb', #exchange/deflators from the IMF
        method = 'gdp',
        source_currency = "USA", #since data is in USD
        target_currency = "EMU", #we want the result in constant EUR
        iso_column = "iso_code",
        date_column = "year",
        source_col = "value",
        target_col = "value_constant",
    ) 
            
    print(df_constant)

This results in a dataframe containing a new column `value_constant` in 2015 constant
prices. In the background, pydeflate takes into account:

- changes in princes, through a gdp deflator in this case
- changes in exchange rates overtime

Pydeflate can also handle data that is expressed in local currency units. In that
case, users can specify `LCU` as the source currency.

.. code:: python

    import pydeflate
    import pandas as pd
    
    #example data
    data = {'iso_code': ['GBR','GBR', 'JPN'],
            'date': [2011, 2015, 2015],
            'value': [100, 100, 100]}
    
    #create an example dataframe, in current local currency units 
    df = pd.DataFrame.from_dict(data)
    
    #convert to USD 2018 constant prices
    df_constant = pydeflate.deflate(
        df = df,
        base_year = 2018,
        source = 'imf', #exchange/deflators from the World Bank
        method = 'pcpi',
        source_currency = "LCU", #since data is in LCU
        target_currency = "USA", #to get data in USD
        iso_column = "iso_code",
        date_column = "date",
        source_col = "value",
        target_col = "value", #to not create a new column
    ) 
            
    print(df_constant)
    
Users can also convert a dataset expressed in constant prices to current prices
using pydeflate. To avoid introducing errors, users should know which methodology/
data was used to create constant prices by the original source. The basic usage is
the same as before, but the `reverse` parameter is set to `True`.

For example, to convert DAC data expressed in 2016 USD constant prices to current
US dollars:

.. code:: python

    import pydeflate
    import pandas as pd
    
    #example data
    data = {'iso_code': ['USA','ITA', 'ITA'],
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
        target_currency = "USA", #to get data in USD
        iso_column = "iso_code",
        date_column = "date",
        source_col = "value",
        target_col = "value_current", 
        reverse = True,   
    ) 
            
    print(df_current)


Data source and method options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A `source` and a `method` for the exchange and price/gdp deflators must be chosen.
The appropriate combination depends on the objectives of the project or the nature 
of the original data.

In terms of price or GDP deflators, pydeflate provides the following `methods`:

- World Bank ("wb"): 

    - `gdp`: in order to use GDP deflators.
    - `gdp_linked`: to use the World Bank's GDP deflator series which has been linked
      to produce a consistent time series to counteract breaks in series over time
      due to changes in base years, sources or methodologies.
    - 'cpi': to use Consumer Price Index data
    
- International Monetary Fund World Economic Outlook ("imf"): 

    - `pcpi`: in order to use Consumer Price Index data.
    - `pcpie`: to use end-of-period Consumer Price Index data (e.g for December each
      year).
      
- OECD Development Assistance Committee ("oecd_dac"): 

    - None: for consistency with how the DAC calculates deflators, only their methodology
      is accepted/used with this data.

The source of the exchange rate data depends on the source selected. Both "imf"
and "wb" use data from the International Monetary Fund (`LCU per US$, yearly average`).
The OECD Development Assistance Committee data uses different exchange rates. When
`oecd_dac` is selected as the source, the OECD DAC exchange rates (`LCU per US$`) are
used. Exchange rates between two non USD currency pairs are derived from the LCU to USD
exchange rates selected.


Additional features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pypdeflate relies on data from the World Bank, IMF and OECD for its calculations. This
data is updated periodically. If the version of the data stored in the user's computer
is older than 50 days, pydeflate will show a warning on import. 

Users can always update the underlying data by using:

.. code:: python

    import pydeflate
    
    pydeflate.update_all_data()
    

Pydeflate also provides users with a tool to exchange figures from one currency to
another, without applying any deflators. This should only be used on numbers expressed
in current prices, however. 

In this version of pydeflate, the dataframe must contain a column with iso3 country
codes called `iso_code`.

For example, to convert numbers in current Local Currency Units (LCU) to current 
Canadian Dollars:

.. code:: python

    import pydeflate
    import pandas as pd
    
    #example data
    data = {'iso_code': ['GBR','CAN', 'JPN'],
            'date': [2011, 2015, 2015],
            'value': [100, 100, 100]}
    
    #create an example dataframe, in current local currency units 
    df = pd.DataFrame.from_dict(data)
    
    #convert to USD 2018 constant prices
    df_can = pydeflate.exchange(
        df = df,
        source_currency = "LCU", #since data is in LCU
        target_currency = "CAN", #to get data in Canadian Dollars
        rates_source = 'wb', #this is the same as IMF exchange rates
        value_column = 'value',
        target_column = 'value_CAN',
        date_column = "date",
    ) 
            
    print(df_can)


Credits
-------

This package relies on data from the following sources:

- OECD DAC: https://www.oecd.org/dac/ (Official Development assistance data (DAC1),
  DAC deflators, and exchange rates used by the DAC)
- IMF World Economic Outlook: https://www.imf.org/en/Publications/WEO (GDP and 
  price deflators)
- World Bank DataBank: https://databank.worldbank.org/home.aspx (exchange rates,
  GDP and price deflators)

This data is provided based on the terms and conditions set by the orignal sources




This tool was packed for pypi with the help of Cookiecutter_ and the 
`audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
