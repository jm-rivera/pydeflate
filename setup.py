#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['pandas>=1.2.1',
                'weo==0.7.0', 
                'numpy>=1.19.2',
                'BeautifulSoup4>=4.0',
                'pandas_datareader>=0.10.0',
                'requests>=2.25.1',
                'requests_cache==0.8.1',
                'pyarrow>=1.19.2'
                'xlrd>=2.0']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3.8', ]

setup(
    author="Jorge Rivera",
    author_email='jorge.rivera@one.org',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Python package to convert current prices figures to constant prices and vice versa",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pydeflate',
    name='pydeflate',
    packages=find_packages(include=['pydeflate', 'pydeflate.*', 'pydeflate.deflate.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/jm-rivera/pydeflate',
    version='1.0.1',
    zip_safe=False,
)
